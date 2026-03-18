// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from dexter_msgs:srv/DispatchItem.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "dexter_msgs/srv/dispatch_item.hpp"


#ifndef DEXTER_MSGS__SRV__DETAIL__DISPATCH_ITEM__TRAITS_HPP_
#define DEXTER_MSGS__SRV__DETAIL__DISPATCH_ITEM__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "dexter_msgs/srv/detail/dispatch_item__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace dexter_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const DispatchItem_Request & msg,
  std::ostream & out)
{
  out << "{";
  // member: mode
  {
    out << "mode: ";
    rosidl_generator_traits::value_to_yaml(msg.mode, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DispatchItem_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: mode
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "mode: ";
    rosidl_generator_traits::value_to_yaml(msg.mode, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DispatchItem_Request & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace dexter_msgs

namespace rosidl_generator_traits
{

[[deprecated("use dexter_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const dexter_msgs::srv::DispatchItem_Request & msg,
  std::ostream & out, size_t indentation = 0)
{
  dexter_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use dexter_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const dexter_msgs::srv::DispatchItem_Request & msg)
{
  return dexter_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<dexter_msgs::srv::DispatchItem_Request>()
{
  return "dexter_msgs::srv::DispatchItem_Request";
}

template<>
inline const char * name<dexter_msgs::srv::DispatchItem_Request>()
{
  return "dexter_msgs/srv/DispatchItem_Request";
}

template<>
struct has_fixed_size<dexter_msgs::srv::DispatchItem_Request>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<dexter_msgs::srv::DispatchItem_Request>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<dexter_msgs::srv::DispatchItem_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace dexter_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const DispatchItem_Response & msg,
  std::ostream & out)
{
  out << "{";
  // member: success
  {
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << ", ";
  }

  // member: item_name
  {
    out << "item_name: ";
    rosidl_generator_traits::value_to_yaml(msg.item_name, out);
    out << ", ";
  }

  // member: item_id
  {
    out << "item_id: ";
    rosidl_generator_traits::value_to_yaml(msg.item_id, out);
    out << ", ";
  }

  // member: slot_number
  {
    out << "slot_number: ";
    rosidl_generator_traits::value_to_yaml(msg.slot_number, out);
    out << ", ";
  }

  // member: expiry_date
  {
    out << "expiry_date: ";
    rosidl_generator_traits::value_to_yaml(msg.expiry_date, out);
    out << ", ";
  }

  // member: message
  {
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DispatchItem_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: success
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "success: ";
    rosidl_generator_traits::value_to_yaml(msg.success, out);
    out << "\n";
  }

  // member: item_name
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "item_name: ";
    rosidl_generator_traits::value_to_yaml(msg.item_name, out);
    out << "\n";
  }

  // member: item_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "item_id: ";
    rosidl_generator_traits::value_to_yaml(msg.item_id, out);
    out << "\n";
  }

  // member: slot_number
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "slot_number: ";
    rosidl_generator_traits::value_to_yaml(msg.slot_number, out);
    out << "\n";
  }

  // member: expiry_date
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "expiry_date: ";
    rosidl_generator_traits::value_to_yaml(msg.expiry_date, out);
    out << "\n";
  }

  // member: message
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "message: ";
    rosidl_generator_traits::value_to_yaml(msg.message, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DispatchItem_Response & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace dexter_msgs

namespace rosidl_generator_traits
{

[[deprecated("use dexter_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const dexter_msgs::srv::DispatchItem_Response & msg,
  std::ostream & out, size_t indentation = 0)
{
  dexter_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use dexter_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const dexter_msgs::srv::DispatchItem_Response & msg)
{
  return dexter_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<dexter_msgs::srv::DispatchItem_Response>()
{
  return "dexter_msgs::srv::DispatchItem_Response";
}

template<>
inline const char * name<dexter_msgs::srv::DispatchItem_Response>()
{
  return "dexter_msgs/srv/DispatchItem_Response";
}

template<>
struct has_fixed_size<dexter_msgs::srv::DispatchItem_Response>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<dexter_msgs::srv::DispatchItem_Response>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<dexter_msgs::srv::DispatchItem_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__traits.hpp"

namespace dexter_msgs
{

namespace srv
{

inline void to_flow_style_yaml(
  const DispatchItem_Event & msg,
  std::ostream & out)
{
  out << "{";
  // member: info
  {
    out << "info: ";
    to_flow_style_yaml(msg.info, out);
    out << ", ";
  }

  // member: request
  {
    if (msg.request.size() == 0) {
      out << "request: []";
    } else {
      out << "request: [";
      size_t pending_items = msg.request.size();
      for (auto item : msg.request) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: response
  {
    if (msg.response.size() == 0) {
      out << "response: []";
    } else {
      out << "response: [";
      size_t pending_items = msg.response.size();
      for (auto item : msg.response) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const DispatchItem_Event & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: info
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "info:\n";
    to_block_style_yaml(msg.info, out, indentation + 2);
  }

  // member: request
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.request.size() == 0) {
      out << "request: []\n";
    } else {
      out << "request:\n";
      for (auto item : msg.request) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: response
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.response.size() == 0) {
      out << "response: []\n";
    } else {
      out << "response:\n";
      for (auto item : msg.response) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const DispatchItem_Event & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace srv

}  // namespace dexter_msgs

namespace rosidl_generator_traits
{

[[deprecated("use dexter_msgs::srv::to_block_style_yaml() instead")]]
inline void to_yaml(
  const dexter_msgs::srv::DispatchItem_Event & msg,
  std::ostream & out, size_t indentation = 0)
{
  dexter_msgs::srv::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use dexter_msgs::srv::to_yaml() instead")]]
inline std::string to_yaml(const dexter_msgs::srv::DispatchItem_Event & msg)
{
  return dexter_msgs::srv::to_yaml(msg);
}

template<>
inline const char * data_type<dexter_msgs::srv::DispatchItem_Event>()
{
  return "dexter_msgs::srv::DispatchItem_Event";
}

template<>
inline const char * name<dexter_msgs::srv::DispatchItem_Event>()
{
  return "dexter_msgs/srv/DispatchItem_Event";
}

template<>
struct has_fixed_size<dexter_msgs::srv::DispatchItem_Event>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<dexter_msgs::srv::DispatchItem_Event>
  : std::integral_constant<bool, has_bounded_size<dexter_msgs::srv::DispatchItem_Request>::value && has_bounded_size<dexter_msgs::srv::DispatchItem_Response>::value && has_bounded_size<service_msgs::msg::ServiceEventInfo>::value> {};

template<>
struct is_message<dexter_msgs::srv::DispatchItem_Event>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<dexter_msgs::srv::DispatchItem>()
{
  return "dexter_msgs::srv::DispatchItem";
}

template<>
inline const char * name<dexter_msgs::srv::DispatchItem>()
{
  return "dexter_msgs/srv/DispatchItem";
}

template<>
struct has_fixed_size<dexter_msgs::srv::DispatchItem>
  : std::integral_constant<
    bool,
    has_fixed_size<dexter_msgs::srv::DispatchItem_Request>::value &&
    has_fixed_size<dexter_msgs::srv::DispatchItem_Response>::value
  >
{
};

template<>
struct has_bounded_size<dexter_msgs::srv::DispatchItem>
  : std::integral_constant<
    bool,
    has_bounded_size<dexter_msgs::srv::DispatchItem_Request>::value &&
    has_bounded_size<dexter_msgs::srv::DispatchItem_Response>::value
  >
{
};

template<>
struct is_service<dexter_msgs::srv::DispatchItem>
  : std::true_type
{
};

template<>
struct is_service_request<dexter_msgs::srv::DispatchItem_Request>
  : std::true_type
{
};

template<>
struct is_service_response<dexter_msgs::srv::DispatchItem_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // DEXTER_MSGS__SRV__DETAIL__DISPATCH_ITEM__TRAITS_HPP_
