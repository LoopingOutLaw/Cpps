// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from dexter_msgs:srv/AddItem.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "dexter_msgs/srv/add_item.hpp"


#ifndef DEXTER_MSGS__SRV__DETAIL__ADD_ITEM__BUILDER_HPP_
#define DEXTER_MSGS__SRV__DETAIL__ADD_ITEM__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "dexter_msgs/srv/detail/add_item__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace dexter_msgs
{

namespace srv
{

namespace builder
{

class Init_AddItem_Request_expiry_ts
{
public:
  explicit Init_AddItem_Request_expiry_ts(::dexter_msgs::srv::AddItem_Request & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::srv::AddItem_Request expiry_ts(::dexter_msgs::srv::AddItem_Request::_expiry_ts_type arg)
  {
    msg_.expiry_ts = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::srv::AddItem_Request msg_;
};

class Init_AddItem_Request_slot
{
public:
  explicit Init_AddItem_Request_slot(::dexter_msgs::srv::AddItem_Request & msg)
  : msg_(msg)
  {}
  Init_AddItem_Request_expiry_ts slot(::dexter_msgs::srv::AddItem_Request::_slot_type arg)
  {
    msg_.slot = std::move(arg);
    return Init_AddItem_Request_expiry_ts(msg_);
  }

private:
  ::dexter_msgs::srv::AddItem_Request msg_;
};

class Init_AddItem_Request_item_name
{
public:
  Init_AddItem_Request_item_name()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AddItem_Request_slot item_name(::dexter_msgs::srv::AddItem_Request::_item_name_type arg)
  {
    msg_.item_name = std::move(arg);
    return Init_AddItem_Request_slot(msg_);
  }

private:
  ::dexter_msgs::srv::AddItem_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::srv::AddItem_Request>()
{
  return dexter_msgs::srv::builder::Init_AddItem_Request_item_name();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace srv
{

namespace builder
{

class Init_AddItem_Response_message
{
public:
  explicit Init_AddItem_Response_message(::dexter_msgs::srv::AddItem_Response & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::srv::AddItem_Response message(::dexter_msgs::srv::AddItem_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::srv::AddItem_Response msg_;
};

class Init_AddItem_Response_item_id
{
public:
  explicit Init_AddItem_Response_item_id(::dexter_msgs::srv::AddItem_Response & msg)
  : msg_(msg)
  {}
  Init_AddItem_Response_message item_id(::dexter_msgs::srv::AddItem_Response::_item_id_type arg)
  {
    msg_.item_id = std::move(arg);
    return Init_AddItem_Response_message(msg_);
  }

private:
  ::dexter_msgs::srv::AddItem_Response msg_;
};

class Init_AddItem_Response_success
{
public:
  Init_AddItem_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AddItem_Response_item_id success(::dexter_msgs::srv::AddItem_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_AddItem_Response_item_id(msg_);
  }

private:
  ::dexter_msgs::srv::AddItem_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::srv::AddItem_Response>()
{
  return dexter_msgs::srv::builder::Init_AddItem_Response_success();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace srv
{

namespace builder
{

class Init_AddItem_Event_response
{
public:
  explicit Init_AddItem_Event_response(::dexter_msgs::srv::AddItem_Event & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::srv::AddItem_Event response(::dexter_msgs::srv::AddItem_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::srv::AddItem_Event msg_;
};

class Init_AddItem_Event_request
{
public:
  explicit Init_AddItem_Event_request(::dexter_msgs::srv::AddItem_Event & msg)
  : msg_(msg)
  {}
  Init_AddItem_Event_response request(::dexter_msgs::srv::AddItem_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_AddItem_Event_response(msg_);
  }

private:
  ::dexter_msgs::srv::AddItem_Event msg_;
};

class Init_AddItem_Event_info
{
public:
  Init_AddItem_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_AddItem_Event_request info(::dexter_msgs::srv::AddItem_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_AddItem_Event_request(msg_);
  }

private:
  ::dexter_msgs::srv::AddItem_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::srv::AddItem_Event>()
{
  return dexter_msgs::srv::builder::Init_AddItem_Event_info();
}

}  // namespace dexter_msgs

#endif  // DEXTER_MSGS__SRV__DETAIL__ADD_ITEM__BUILDER_HPP_
