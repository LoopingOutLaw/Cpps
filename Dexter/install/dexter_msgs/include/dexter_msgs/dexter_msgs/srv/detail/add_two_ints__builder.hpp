// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from dexter_msgs:srv/AddTwoInts.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "dexter_msgs/srv/add_two_ints.hpp"


#ifndef DEXTER_MSGS__SRV__DETAIL__ADD_TWO_INTS__BUILDER_HPP_
#define DEXTER_MSGS__SRV__DETAIL__ADD_TWO_INTS__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "dexter_msgs/srv/detail/add_two_ints__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace dexter_msgs
{

namespace srv
{

namespace builder
{

class Init_AddTwoInts_Request_b
{
public:
  explicit Init_AddTwoInts_Request_b(::dexter_msgs::srv::AddTwoInts_Request & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::srv::AddTwoInts_Request b(::dexter_msgs::srv::AddTwoInts_Request::_b_type arg)
  {
    msg_.b = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::srv::AddTwoInts_Request msg_;
};

class Init_AddTwoInts_Request_a
{
public:
  Init_AddTwoInts_Request_a()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AddTwoInts_Request_b a(::dexter_msgs::srv::AddTwoInts_Request::_a_type arg)
  {
    msg_.a = std::move(arg);
    return Init_AddTwoInts_Request_b(msg_);
  }

private:
  ::dexter_msgs::srv::AddTwoInts_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::srv::AddTwoInts_Request>()
{
  return dexter_msgs::srv::builder::Init_AddTwoInts_Request_a();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace srv
{

namespace builder
{

class Init_AddTwoInts_Response_sum
{
public:
  Init_AddTwoInts_Response_sum()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::dexter_msgs::srv::AddTwoInts_Response sum(::dexter_msgs::srv::AddTwoInts_Response::_sum_type arg)
  {
    msg_.sum = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::srv::AddTwoInts_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::srv::AddTwoInts_Response>()
{
  return dexter_msgs::srv::builder::Init_AddTwoInts_Response_sum();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace srv
{

namespace builder
{

class Init_AddTwoInts_Event_response
{
public:
  explicit Init_AddTwoInts_Event_response(::dexter_msgs::srv::AddTwoInts_Event & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::srv::AddTwoInts_Event response(::dexter_msgs::srv::AddTwoInts_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::srv::AddTwoInts_Event msg_;
};

class Init_AddTwoInts_Event_request
{
public:
  explicit Init_AddTwoInts_Event_request(::dexter_msgs::srv::AddTwoInts_Event & msg)
  : msg_(msg)
  {}
  Init_AddTwoInts_Event_response request(::dexter_msgs::srv::AddTwoInts_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_AddTwoInts_Event_response(msg_);
  }

private:
  ::dexter_msgs::srv::AddTwoInts_Event msg_;
};

class Init_AddTwoInts_Event_info
{
public:
  Init_AddTwoInts_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AddTwoInts_Event_request info(::dexter_msgs::srv::AddTwoInts_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_AddTwoInts_Event_request(msg_);
  }

private:
  ::dexter_msgs::srv::AddTwoInts_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::srv::AddTwoInts_Event>()
{
  return dexter_msgs::srv::builder::Init_AddTwoInts_Event_info();
}

}  // namespace dexter_msgs

#endif  // DEXTER_MSGS__SRV__DETAIL__ADD_TWO_INTS__BUILDER_HPP_
