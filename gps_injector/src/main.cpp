#include <memory>

#include <rclcpp/rclcpp.hpp>
#include "GPSInjector.hpp"

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<GPSInjector>());
    rclcpp::shutdown();
    return 0;
}
