#!/usr/bin/env python3
"""
Stub Isaac twin validation service.
Replace body with Isaac Sim ROS2 bridge when Omniverse is connected.
"""

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class TwinValidateNode(Node):
    def __init__(self) -> None:
        super().__init__("physical_ai_twin_validate")
        self.create_service(
            Trigger, "/physical_ai/twin/validate_motion", self._validate
        )
        self.get_logger().info("Twin validate service ready (stub — always approves)")

    def _validate(self, request, response):
        response.success = True
        response.message = "Stub twin validated motion (connect Isaac Sim for real check)"
        return response


def main():
    rclpy.init()
    node = TwinValidateNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
