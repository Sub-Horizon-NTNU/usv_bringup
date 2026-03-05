#include <chrono>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/range.hpp>

class GPSInjector : public rclcpp::Node
{
public:
    GPSInjector() : Node("gps_injector")
    {
    range_publisher_ = this->create_publisher<sensor_msgs::msg::Range>("/mavros/rangefinder_sub", 10);

    range_publish_timer_ = this->create_wall_timer(
        std::chrono::milliseconds(100),
        std::bind(&GPSInjector::publish_range, this));
    }

    void publish_range(){
        sensor_msgs::msg::Range range;
        range.radiation_type = 0;
        range.min_range = 0.0f;
        range.max_range = 10.0f;
        range.range = 1.0f;
        range.field_of_view = 3.14;
        
        range_publisher_->publish(range);
        
    

    }

private:
rclcpp::Publisher<sensor_msgs::msg::Range>::SharedPtr range_publisher_;
rclcpp::TimerBase::SharedPtr range_publish_timer_;

};
