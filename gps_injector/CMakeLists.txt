cmake_minimum_required(VERSION 3.8)
project(gps_injector)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(mavros_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)


add_executable(gps_injector src/main.cpp
  src/GPSInjector.cpp
)
target_include_directories(gps_injector PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
ament_target_dependencies(gps_injector 
  rclcpp
  mavros_msgs
)

install(TARGETS gps_injector
  DESTINATION lib/${PROJECT_NAME}
)


install(DIRECTORY include/
  DESTINATION include
)



ament_package()
