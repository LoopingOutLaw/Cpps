// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from dexter_msgs:srv/EulerToQuaternion.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "dexter_msgs/srv/euler_to_quaternion.h"


#ifndef DEXTER_MSGS__SRV__DETAIL__EULER_TO_QUATERNION__STRUCT_H_
#define DEXTER_MSGS__SRV__DETAIL__EULER_TO_QUATERNION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in srv/EulerToQuaternion in the package dexter_msgs.
typedef struct dexter_msgs__srv__EulerToQuaternion_Request
{
  double roll;
  double pitch;
  double yaw;
} dexter_msgs__srv__EulerToQuaternion_Request;

// Struct for a sequence of dexter_msgs__srv__EulerToQuaternion_Request.
typedef struct dexter_msgs__srv__EulerToQuaternion_Request__Sequence
{
  dexter_msgs__srv__EulerToQuaternion_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dexter_msgs__srv__EulerToQuaternion_Request__Sequence;

// Constants defined in the message

/// Struct defined in srv/EulerToQuaternion in the package dexter_msgs.
typedef struct dexter_msgs__srv__EulerToQuaternion_Response
{
  double x;
  double y;
  double z;
  double w;
} dexter_msgs__srv__EulerToQuaternion_Response;

// Struct for a sequence of dexter_msgs__srv__EulerToQuaternion_Response.
typedef struct dexter_msgs__srv__EulerToQuaternion_Response__Sequence
{
  dexter_msgs__srv__EulerToQuaternion_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dexter_msgs__srv__EulerToQuaternion_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  dexter_msgs__srv__EulerToQuaternion_Event__request__MAX_SIZE = 1
};
// response
enum
{
  dexter_msgs__srv__EulerToQuaternion_Event__response__MAX_SIZE = 1
};

/// Struct defined in srv/EulerToQuaternion in the package dexter_msgs.
typedef struct dexter_msgs__srv__EulerToQuaternion_Event
{
  service_msgs__msg__ServiceEventInfo info;
  dexter_msgs__srv__EulerToQuaternion_Request__Sequence request;
  dexter_msgs__srv__EulerToQuaternion_Response__Sequence response;
} dexter_msgs__srv__EulerToQuaternion_Event;

// Struct for a sequence of dexter_msgs__srv__EulerToQuaternion_Event.
typedef struct dexter_msgs__srv__EulerToQuaternion_Event__Sequence
{
  dexter_msgs__srv__EulerToQuaternion_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dexter_msgs__srv__EulerToQuaternion_Event__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DEXTER_MSGS__SRV__DETAIL__EULER_TO_QUATERNION__STRUCT_H_
