// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from dexter_msgs:srv/DispatchItem.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "dexter_msgs/srv/dispatch_item.hpp"


#ifndef DEXTER_MSGS__SRV__DETAIL__DISPATCH_ITEM__BUILDER_HPP_
#define DEXTER_MSGS__SRV__DETAIL__DISPATCH_ITEM__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "dexter_msgs/srv/detail/dispatch_item__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace dexter_msgs
{

namespace srv
{

namespace builder
{

class Init_DispatchItem_Request_mode
{
public:
  Init_DispatchItem_Request_mode()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::dexter_msgs::srv::DispatchItem_Request mode(::dexter_msgs::srv::DispatchItem_Request::_mode_type arg)
  {
    msg_.mode = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::srv::DispatchItem_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::srv::DispatchItem_Request>()
{
  return dexter_msgs::srv::builder::Init_DispatchItem_Request_mode();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace srv
{

namespace builder
{

class Init_DispatchItem_Response_message
{
public:
  explicit Init_DispatchItem_Response_message(::dexter_msgs::srv::DispatchItem_Response & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::srv::DispatchItem_Response message(::dexter_msgs::srv::DispatchItem_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::srv::DispatchItem_Response msg_;
};

class Init_DispatchItem_Response_expiry_date
{
public:
  explicit Init_DispatchItem_Response_expiry_date(::dexter_msgs::srv::DispatchItem_Response & msg)
  : msg_(msg)
  {}
  Init_DispatchItem_Response_message expiry_date(::dexter_msgs::srv::DispatchItem_Response::_expiry_date_type arg)
  {
    msg_.expiry_date = std::move(arg);
    return Init_DispatchItem_Response_message(msg_);
  }

private:
  ::dexter_msgs::srv::DispatchItem_Response msg_;
};

class Init_DispatchItem_Response_slot_number
{
public:
  explicit Init_DispatchItem_Response_slot_number(::dexter_msgs::srv::DispatchItem_Response & msg)
  : msg_(msg)
  {}
  Init_DispatchItem_Response_expiry_date slot_number(::dexter_msgs::srv::DispatchItem_Response::_slot_number_type arg)
  {
    msg_.slot_number = std::move(arg);
    return Init_DispatchItem_Response_expiry_date(msg_);
  }

private:
  ::dexter_msgs::srv::DispatchItem_Response msg_;
};

class Init_DispatchItem_Response_item_id
{
public:
  explicit Init_DispatchItem_Response_item_id(::dexter_msgs::srv::DispatchItem_Response & msg)
  : msg_(msg)
  {}
  Init_DispatchItem_Response_slot_number item_id(::dexter_msgs::srv::DispatchItem_Response::_item_id_type arg)
  {
    msg_.item_id = std::move(arg);
    return Init_DispatchItem_Response_slot_number(msg_);
  }

private:
  ::dexter_msgs::srv::DispatchItem_Response msg_;
};

class Init_DispatchItem_Response_item_name
{
public:
  explicit Init_DispatchItem_Response_item_name(::dexter_msgs::srv::DispatchItem_Response & msg)
  : msg_(msg)
  {}
  Init_DispatchItem_Response_item_id item_name(::dexter_msgs::srv::DispatchItem_Response::_item_name_type arg)
  {
    msg_.item_name = std::move(arg);
    return Init_DispatchItem_Response_item_id(msg_);
  }

private:
  ::dexter_msgs::srv::DispatchItem_Response msg_;
};

class Init_DispatchItem_Response_success
{
public:
  Init_DispatchItem_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DispatchItem_Response_item_name success(::dexter_msgs::srv::DispatchItem_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_DispatchItem_Response_item_name(msg_);
  }

private:
  ::dexter_msgs::srv::DispatchItem_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::srv::DispatchItem_Response>()
{
  return dexter_msgs::srv::builder::Init_DispatchItem_Response_success();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace srv
{

namespace builder
{

class Init_DispatchItem_Event_response
{
public:
  explicit Init_DispatchItem_Event_response(::dexter_msgs::srv::DispatchItem_Event & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::srv::DispatchItem_Event response(::dexter_msgs::srv::DispatchItem_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::srv::DispatchItem_Event msg_;
};

class Init_DispatchItem_Event_request
{
public:
  explicit Init_DispatchItem_Event_request(::dexter_msgs::srv::DispatchItem_Event & msg)
  : msg_(msg)
  {}
  Init_DispatchItem_Event_response request(::dexter_msgs::srv::DispatchItem_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_DispatchItem_Event_response(msg_);
  }

private:
  ::dexter_msgs::srv::DispatchItem_Event msg_;
};

class Init_DispatchItem_Event_info
{
public:
  Init_DispatchItem_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DispatchItem_Event_request info(::dexter_msgs::srv::DispatchItem_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_DispatchItem_Event_request(msg_);
  }

private:
  ::dexter_msgs::srv::DispatchItem_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::srv::DispatchItem_Event>()
{
  return dexter_msgs::srv::builder::Init_DispatchItem_Event_info();
}

}  // namespace dexter_msgs

#endif  // DEXTER_MSGS__SRV__DETAIL__DISPATCH_ITEM__BUILDER_HPP_
