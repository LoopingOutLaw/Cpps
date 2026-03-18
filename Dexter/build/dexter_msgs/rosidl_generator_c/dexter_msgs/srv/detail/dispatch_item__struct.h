// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from dexter_msgs:srv/DispatchItem.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "dexter_msgs/srv/dispatch_item.h"


#ifndef DEXTER_MSGS__SRV__DETAIL__DISPATCH_ITEM__STRUCT_H_
#define DEXTER_MSGS__SRV__DETAIL__DISPATCH_ITEM__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'mode'
#include "rosidl_runtime_c/string.h"

/// Struct defined in srv/DispatchItem in the package dexter_msgs.
typedef struct dexter_msgs__srv__DispatchItem_Request
{
  /// "FIFO" or "FEFO"
  rosidl_runtime_c__String mode;
} dexter_msgs__srv__DispatchItem_Request;

// Struct for a sequence of dexter_msgs__srv__DispatchItem_Request.
typedef struct dexter_msgs__srv__DispatchItem_Request__Sequence
{
  dexter_msgs__srv__DispatchItem_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dexter_msgs__srv__DispatchItem_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'item_name'
// Member 'item_id'
// Member 'expiry_date'
// Member 'message'
// already included above
// #include "rosidl_runtime_c/string.h"

/// Struct defined in srv/DispatchItem in the package dexter_msgs.
typedef struct dexter_msgs__srv__DispatchItem_Response
{
  bool success;
  rosidl_runtime_c__String item_name;
  rosidl_runtime_c__String item_id;
  int32_t slot_number;
  rosidl_runtime_c__String expiry_date;
  rosidl_runtime_c__String message;
} dexter_msgs__srv__DispatchItem_Response;

// Struct for a sequence of dexter_msgs__srv__DispatchItem_Response.
typedef struct dexter_msgs__srv__DispatchItem_Response__Sequence
{
  dexter_msgs__srv__DispatchItem_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dexter_msgs__srv__DispatchItem_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  dexter_msgs__srv__DispatchItem_Event__request__MAX_SIZE = 1
};
// response
enum
{
  dexter_msgs__srv__DispatchItem_Event__response__MAX_SIZE = 1
};

/// Struct defined in srv/DispatchItem in the package dexter_msgs.
typedef struct dexter_msgs__srv__DispatchItem_Event
{
  service_msgs__msg__ServiceEventInfo info;
  dexter_msgs__srv__DispatchItem_Request__Sequence request;
  dexter_msgs__srv__DispatchItem_Response__Sequence response;
} dexter_msgs__srv__DispatchItem_Event;

// Struct for a sequence of dexter_msgs__srv__DispatchItem_Event.
typedef struct dexter_msgs__srv__DispatchItem_Event__Sequence
{
  dexter_msgs__srv__DispatchItem_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dexter_msgs__srv__DispatchItem_Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DEXTER_MSGS__SRV__DETAIL__DISPATCH_ITEM__STRUCT_H_
