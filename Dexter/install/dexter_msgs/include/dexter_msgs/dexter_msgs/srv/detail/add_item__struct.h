// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from dexter_msgs:srv/AddItem.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "dexter_msgs/srv/add_item.h"


#ifndef DEXTER_MSGS__SRV__DETAIL__ADD_ITEM__STRUCT_H_
#define DEXTER_MSGS__SRV__DETAIL__ADD_ITEM__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'item_name'
// Member 'expiry_ts'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/AddItem in the package dexter_msgs.
typedef struct dexter_msgs__srv__AddItem_Request
{
  rosidl_runtime_c__String item_name;
  int32_t slot;
  /// Unix timestamp as string; empty = no expiry
  rosidl_runtime_c__String expiry_ts;
} dexter_msgs__srv__AddItem_Request;

// Struct for a sequence of dexter_msgs__srv__AddItem_Request.
typedef struct dexter_msgs__srv__AddItem_Request__Sequence
{
  dexter_msgs__srv__AddItem_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dexter_msgs__srv__AddItem_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'item_id'
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/AddItem in the package dexter_msgs.
typedef struct dexter_msgs__srv__AddItem_Response
{
  bool success;
  rosidl_runtime_c__String item_id;
  rosidl_runtime_c__String message;
} dexter_msgs__srv__AddItem_Response;

// Struct for a sequence of dexter_msgs__srv__AddItem_Response.
typedef struct dexter_msgs__srv__AddItem_Response__Sequence
{
  dexter_msgs__srv__AddItem_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dexter_msgs__srv__AddItem_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  dexter_msgs__srv__AddItem_Event__request__MAX_SIZE = 1
};
// response
enum
{
  dexter_msgs__srv__AddItem_Event__response__MAX_SIZE = 1
};

/// Struct defined in srv/AddItem in the package dexter_msgs.
typedef struct dexter_msgs__srv__AddItem_Event
{
  service_msgs__msg__ServiceEventInfo info;
  dexter_msgs__srv__AddItem_Request__Sequence request;
  dexter_msgs__srv__AddItem_Response__Sequence response;
} dexter_msgs__srv__AddItem_Event;

// Struct for a sequence of dexter_msgs__srv__AddItem_Event.
typedef struct dexter_msgs__srv__AddItem_Event__Sequence
{
  dexter_msgs__srv__AddItem_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dexter_msgs__srv__AddItem_Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DEXTER_MSGS__SRV__DETAIL__ADD_ITEM__STRUCT_H_
