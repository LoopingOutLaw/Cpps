// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from dexter_msgs:srv/AddItem.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "dexter_msgs/srv/detail/add_item__rosidl_typesupport_introspection_c.h"
#include "dexter_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "dexter_msgs/srv/detail/add_item__functions.h"
#include "dexter_msgs/srv/detail/add_item__struct.h"


// Include directives for member types
// Member `item_name`
// Member `expiry_ts`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  dexter_msgs__srv__AddItem_Request__init(message_memory);
}

void dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_fini_function(void * message_memory)
{
  dexter_msgs__srv__AddItem_Request__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_message_member_array[3] = {
  {
    "item_name",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dexter_msgs__srv__AddItem_Request, item_name),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "slot",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_INT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dexter_msgs__srv__AddItem_Request, slot),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "expiry_ts",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dexter_msgs__srv__AddItem_Request, expiry_ts),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_message_members = {
  "dexter_msgs__srv",  // message namespace
  "AddItem_Request",  // message name
  3,  // number of fields
  sizeof(dexter_msgs__srv__AddItem_Request),
  false,  // has_any_key_member_
  dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_message_member_array,  // message members
  dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_init_function,  // function to initialize message memory (memory has to be allocated)
  dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_message_type_support_handle = {
  0,
  &dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_message_members,
  get_message_typesupport_handle_function,
  &dexter_msgs__srv__AddItem_Request__get_type_hash,
  &dexter_msgs__srv__AddItem_Request__get_type_description,
  &dexter_msgs__srv__AddItem_Request__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_dexter_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem_Request)() {
  if (!dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_message_type_support_handle.typesupport_identifier) {
    dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "dexter_msgs/srv/detail/add_item__rosidl_typesupport_introspection_c.h"
// already included above
// #include "dexter_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "dexter_msgs/srv/detail/add_item__functions.h"
// already included above
// #include "dexter_msgs/srv/detail/add_item__struct.h"


// Include directives for member types
// Member `item_id`
// Member `message`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  dexter_msgs__srv__AddItem_Response__init(message_memory);
}

void dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_fini_function(void * message_memory)
{
  dexter_msgs__srv__AddItem_Response__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_message_member_array[3] = {
  {
    "success",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dexter_msgs__srv__AddItem_Response, success),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "item_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dexter_msgs__srv__AddItem_Response, item_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "message",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dexter_msgs__srv__AddItem_Response, message),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_message_members = {
  "dexter_msgs__srv",  // message namespace
  "AddItem_Response",  // message name
  3,  // number of fields
  sizeof(dexter_msgs__srv__AddItem_Response),
  false,  // has_any_key_member_
  dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_message_member_array,  // message members
  dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_init_function,  // function to initialize message memory (memory has to be allocated)
  dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_message_type_support_handle = {
  0,
  &dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_message_members,
  get_message_typesupport_handle_function,
  &dexter_msgs__srv__AddItem_Response__get_type_hash,
  &dexter_msgs__srv__AddItem_Response__get_type_description,
  &dexter_msgs__srv__AddItem_Response__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_dexter_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem_Response)() {
  if (!dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_message_type_support_handle.typesupport_identifier) {
    dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

// already included above
// #include <stddef.h>
// already included above
// #include "dexter_msgs/srv/detail/add_item__rosidl_typesupport_introspection_c.h"
// already included above
// #include "dexter_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "rosidl_typesupport_introspection_c/field_types.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
// already included above
// #include "rosidl_typesupport_introspection_c/message_introspection.h"
// already included above
// #include "dexter_msgs/srv/detail/add_item__functions.h"
// already included above
// #include "dexter_msgs/srv/detail/add_item__struct.h"


// Include directives for member types
// Member `info`
#include "service_msgs/msg/service_event_info.h"
// Member `info`
#include "service_msgs/msg/detail/service_event_info__rosidl_typesupport_introspection_c.h"
// Member `request`
// Member `response`
#include "dexter_msgs/srv/add_item.h"
// Member `request`
// Member `response`
// already included above
// #include "dexter_msgs/srv/detail/add_item__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  dexter_msgs__srv__AddItem_Event__init(message_memory);
}

void dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_fini_function(void * message_memory)
{
  dexter_msgs__srv__AddItem_Event__fini(message_memory);
}

size_t dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__size_function__AddItem_Event__request(
  const void * untyped_member)
{
  const dexter_msgs__srv__AddItem_Request__Sequence * member =
    (const dexter_msgs__srv__AddItem_Request__Sequence *)(untyped_member);
  return member->size;
}

const void * dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_const_function__AddItem_Event__request(
  const void * untyped_member, size_t index)
{
  const dexter_msgs__srv__AddItem_Request__Sequence * member =
    (const dexter_msgs__srv__AddItem_Request__Sequence *)(untyped_member);
  return &member->data[index];
}

void * dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_function__AddItem_Event__request(
  void * untyped_member, size_t index)
{
  dexter_msgs__srv__AddItem_Request__Sequence * member =
    (dexter_msgs__srv__AddItem_Request__Sequence *)(untyped_member);
  return &member->data[index];
}

void dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__fetch_function__AddItem_Event__request(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const dexter_msgs__srv__AddItem_Request * item =
    ((const dexter_msgs__srv__AddItem_Request *)
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_const_function__AddItem_Event__request(untyped_member, index));
  dexter_msgs__srv__AddItem_Request * value =
    (dexter_msgs__srv__AddItem_Request *)(untyped_value);
  *value = *item;
}

void dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__assign_function__AddItem_Event__request(
  void * untyped_member, size_t index, const void * untyped_value)
{
  dexter_msgs__srv__AddItem_Request * item =
    ((dexter_msgs__srv__AddItem_Request *)
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_function__AddItem_Event__request(untyped_member, index));
  const dexter_msgs__srv__AddItem_Request * value =
    (const dexter_msgs__srv__AddItem_Request *)(untyped_value);
  *item = *value;
}

bool dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__resize_function__AddItem_Event__request(
  void * untyped_member, size_t size)
{
  dexter_msgs__srv__AddItem_Request__Sequence * member =
    (dexter_msgs__srv__AddItem_Request__Sequence *)(untyped_member);
  dexter_msgs__srv__AddItem_Request__Sequence__fini(member);
  return dexter_msgs__srv__AddItem_Request__Sequence__init(member, size);
}

size_t dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__size_function__AddItem_Event__response(
  const void * untyped_member)
{
  const dexter_msgs__srv__AddItem_Response__Sequence * member =
    (const dexter_msgs__srv__AddItem_Response__Sequence *)(untyped_member);
  return member->size;
}

const void * dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_const_function__AddItem_Event__response(
  const void * untyped_member, size_t index)
{
  const dexter_msgs__srv__AddItem_Response__Sequence * member =
    (const dexter_msgs__srv__AddItem_Response__Sequence *)(untyped_member);
  return &member->data[index];
}

void * dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_function__AddItem_Event__response(
  void * untyped_member, size_t index)
{
  dexter_msgs__srv__AddItem_Response__Sequence * member =
    (dexter_msgs__srv__AddItem_Response__Sequence *)(untyped_member);
  return &member->data[index];
}

void dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__fetch_function__AddItem_Event__response(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const dexter_msgs__srv__AddItem_Response * item =
    ((const dexter_msgs__srv__AddItem_Response *)
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_const_function__AddItem_Event__response(untyped_member, index));
  dexter_msgs__srv__AddItem_Response * value =
    (dexter_msgs__srv__AddItem_Response *)(untyped_value);
  *value = *item;
}

void dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__assign_function__AddItem_Event__response(
  void * untyped_member, size_t index, const void * untyped_value)
{
  dexter_msgs__srv__AddItem_Response * item =
    ((dexter_msgs__srv__AddItem_Response *)
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_function__AddItem_Event__response(untyped_member, index));
  const dexter_msgs__srv__AddItem_Response * value =
    (const dexter_msgs__srv__AddItem_Response *)(untyped_value);
  *item = *value;
}

bool dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__resize_function__AddItem_Event__response(
  void * untyped_member, size_t size)
{
  dexter_msgs__srv__AddItem_Response__Sequence * member =
    (dexter_msgs__srv__AddItem_Response__Sequence *)(untyped_member);
  dexter_msgs__srv__AddItem_Response__Sequence__fini(member);
  return dexter_msgs__srv__AddItem_Response__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_member_array[3] = {
  {
    "info",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dexter_msgs__srv__AddItem_Event, info),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "request",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is key
    true,  // is array
    1,  // array size
    true,  // is upper bound
    offsetof(dexter_msgs__srv__AddItem_Event, request),  // bytes offset in struct
    NULL,  // default value
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__size_function__AddItem_Event__request,  // size() function pointer
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_const_function__AddItem_Event__request,  // get_const(index) function pointer
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_function__AddItem_Event__request,  // get(index) function pointer
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__fetch_function__AddItem_Event__request,  // fetch(index, &value) function pointer
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__assign_function__AddItem_Event__request,  // assign(index, value) function pointer
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__resize_function__AddItem_Event__request  // resize(index) function pointer
  },
  {
    "response",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is key
    true,  // is array
    1,  // array size
    true,  // is upper bound
    offsetof(dexter_msgs__srv__AddItem_Event, response),  // bytes offset in struct
    NULL,  // default value
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__size_function__AddItem_Event__response,  // size() function pointer
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_const_function__AddItem_Event__response,  // get_const(index) function pointer
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__get_function__AddItem_Event__response,  // get(index) function pointer
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__fetch_function__AddItem_Event__response,  // fetch(index, &value) function pointer
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__assign_function__AddItem_Event__response,  // assign(index, value) function pointer
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__resize_function__AddItem_Event__response  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_members = {
  "dexter_msgs__srv",  // message namespace
  "AddItem_Event",  // message name
  3,  // number of fields
  sizeof(dexter_msgs__srv__AddItem_Event),
  false,  // has_any_key_member_
  dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_member_array,  // message members
  dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_init_function,  // function to initialize message memory (memory has to be allocated)
  dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_type_support_handle = {
  0,
  &dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_members,
  get_message_typesupport_handle_function,
  &dexter_msgs__srv__AddItem_Event__get_type_hash,
  &dexter_msgs__srv__AddItem_Event__get_type_description,
  &dexter_msgs__srv__AddItem_Event__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_dexter_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem_Event)() {
  dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, service_msgs, msg, ServiceEventInfo)();
  dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem_Request)();
  dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_member_array[2].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem_Response)();
  if (!dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_type_support_handle.typesupport_identifier) {
    dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif

#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "dexter_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
// already included above
// #include "dexter_msgs/srv/detail/add_item__rosidl_typesupport_introspection_c.h"
// already included above
// #include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/service_introspection.h"

// this is intentionally not const to allow initialization later to prevent an initialization race
static rosidl_typesupport_introspection_c__ServiceMembers dexter_msgs__srv__detail__add_item__rosidl_typesupport_introspection_c__AddItem_service_members = {
  "dexter_msgs__srv",  // service namespace
  "AddItem",  // service name
  // the following fields are initialized below on first access
  NULL,  // request message
  // dexter_msgs__srv__detail__add_item__rosidl_typesupport_introspection_c__AddItem_Request_message_type_support_handle,
  NULL,  // response message
  // dexter_msgs__srv__detail__add_item__rosidl_typesupport_introspection_c__AddItem_Response_message_type_support_handle
  NULL  // event_message
  // dexter_msgs__srv__detail__add_item__rosidl_typesupport_introspection_c__AddItem_Response_message_type_support_handle
};


static rosidl_service_type_support_t dexter_msgs__srv__detail__add_item__rosidl_typesupport_introspection_c__AddItem_service_type_support_handle = {
  0,
  &dexter_msgs__srv__detail__add_item__rosidl_typesupport_introspection_c__AddItem_service_members,
  get_service_typesupport_handle_function,
  &dexter_msgs__srv__AddItem_Request__rosidl_typesupport_introspection_c__AddItem_Request_message_type_support_handle,
  &dexter_msgs__srv__AddItem_Response__rosidl_typesupport_introspection_c__AddItem_Response_message_type_support_handle,
  &dexter_msgs__srv__AddItem_Event__rosidl_typesupport_introspection_c__AddItem_Event_message_type_support_handle,
  ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_CREATE_EVENT_MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c,
    dexter_msgs,
    srv,
    AddItem
  ),
  ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_DESTROY_EVENT_MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c,
    dexter_msgs,
    srv,
    AddItem
  ),
  &dexter_msgs__srv__AddItem__get_type_hash,
  &dexter_msgs__srv__AddItem__get_type_description,
  &dexter_msgs__srv__AddItem__get_type_description_sources,
};

// Forward declaration of message type support functions for service members
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem_Request)(void);

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem_Response)(void);

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem_Event)(void);

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_dexter_msgs
const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem)(void) {
  if (!dexter_msgs__srv__detail__add_item__rosidl_typesupport_introspection_c__AddItem_service_type_support_handle.typesupport_identifier) {
    dexter_msgs__srv__detail__add_item__rosidl_typesupport_introspection_c__AddItem_service_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  rosidl_typesupport_introspection_c__ServiceMembers * service_members =
    (rosidl_typesupport_introspection_c__ServiceMembers *)dexter_msgs__srv__detail__add_item__rosidl_typesupport_introspection_c__AddItem_service_type_support_handle.data;

  if (!service_members->request_members_) {
    service_members->request_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem_Request)()->data;
  }
  if (!service_members->response_members_) {
    service_members->response_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem_Response)()->data;
  }
  if (!service_members->event_members_) {
    service_members->event_members_ =
      (const rosidl_typesupport_introspection_c__MessageMembers *)
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dexter_msgs, srv, AddItem_Event)()->data;
  }

  return &dexter_msgs__srv__detail__add_item__rosidl_typesupport_introspection_c__AddItem_service_type_support_handle;
}
