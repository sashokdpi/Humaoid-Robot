cmake_minimum_required(VERSION 3.8)
project(physical_ai_bringup)

find_package(ament_cmake REQUIRED)
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})
ament_package()
