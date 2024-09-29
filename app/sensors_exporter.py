#!/usr/bin/env python3
import json
import os
import sys
import time
import logging

from lywsd03mmc import Lywsd03mmcClient
from prometheus_client import Gauge, start_http_server
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


TEMPERATURE_GAUGE = Gauge(name='sensor_temperature_celsius',
                          documentation='Temperature of the sensor in Celsius',
                          labelnames=['device_id'])
HUMIDITY_GAUGE = Gauge(name='sensor_humidity_percent',
                       documentation='Humidity percentage of the sensor',
                       labelnames=['device_id'])
BATTERY_GAUGE = Gauge(name='sensor_battery_percent',
                      documentation='Battery percentage of the sensor',
                      labelnames=['device_id'])

class SensorService:
    def __init__(self, devices: dict):
        self.clients = {name: Lywsd03mmcClient(mac) for name, mac in devices.items()}

    def try_fetch_data(self):
        with ThreadPoolExecutor() as executor:
            logging.info("Connecting to sensors" + str(self.clients.keys()))
            futures = {
                name: executor.submit(self._try_update_client, client) for name, client in self.clients.items()
            }
            for name, f in futures.items():
                sensor = f.result()
                if sensor is not None:
                    logging.info(f"{name}: {sensor.temperature}°C, humidity: {sensor.humidity}%, battery: {sensor.battery}%")
                    TEMPERATURE_GAUGE.labels(device_id=name).set(sensor.temperature)
                    HUMIDITY_GAUGE.labels(device_id=name).set(sensor.humidity)
                    BATTERY_GAUGE.labels(device_id=name).set(sensor.battery)
                else:
                    logging.info(f"Failed to fetch data for {name}")

    @staticmethod
    def _try_update_client(client):
        try:
            return client.data
        except Exception as e:
            logging.warn(f"Failed to fetch data for {client}: {e}")


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='Read data from Xiaomi Mi LYWSD03MMC sensors')
    parser.add_argument('--config',
                        type=str,
                        help='Json with devices ({name: mac, [name: mac,]...})',
                        required=True)
    return parser.parse_args()


def run(devices: dict, interval: int):
    # Start HTTP server for Prometheus metrics
    start_http_server(8083)

    sensors = SensorService(devices=devices)
    while True:
        sensors.try_fetch_data()
        time.sleep(interval)


if __name__ == '__main__':
    args = parse_args()

    if not os.path.exists(args.config):
        logging.error(f"Configuration file {args.config} does not exist")
        sys.exit(1)

    with open(args.config, 'r') as f:
        config = json.load(f)
        logging.info("Configuration: " + str(config))

    devices = config.get('devices', {})
    if not devices:
        logging.error("No devices found in the configuration")
        sys.exit(1)
    interval = config.get('interval', 60)
    logging.info(f"Reading data from sensors every {interval} seconds")

    run(devices=devices, interval=interval)
