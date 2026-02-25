#include <chrono>
#include <rclcpp/rclcpp.hpp>
#include <mavros_msgs/msg/gpsinput.hpp>

class GPSInjector : public rclcpp::Node
{
public:
    GPSInjector() : Node("gps_injector")
    {
    gps_publisher_ = this->create_publisher<mavros_msgs::msg::GPSINPUT>("/mavros/gps_input/gps_input", 10);

    gps_publish_timer_ = this->create_wall_timer(
        std::chrono::milliseconds(100),
        std::bind(&GPSInjector::publish_gps, this));
    }

    void publish_gps(){
        mavros_msgs::msg::GPSINPUT gps_input;
        gps_input.fix_type = mavros_msgs::msg::GPSINPUT::GPS_FIX_TYPE_3D_FIX;
        gps_input.lat = 77.0000;
        gps_input.lon = 50.0001;
        gps_input.alt = -1.0;
        gps_input.hdop = 0.00001;
        gps_input.vdop = 0.00001;
        gps_input.yaw = 90;

        gps_publisher_->publish(gps_input);
        
        //gps_input.GPS_FIX_TYPE = mavros_msgs::msg::GPSINPUT::GPS_FIX_TYPE_3D_FIX;
    

    }

private:
rclcpp::Publisher<mavros_msgs::msg::GPSINPUT>::SharedPtr gps_publisher_;
rclcpp::TimerBase::SharedPtr gps_publish_timer_;

};
