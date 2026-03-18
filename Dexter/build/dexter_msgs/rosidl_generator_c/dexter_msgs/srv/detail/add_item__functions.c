// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from dexter_msgs:srv/AddItem.idl
// generated code does not contain a copyright notice
#include "dexter_msgs/srv/detail/add_item__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"

// Include directives for member types
// Member `item_name`
// Member `expiry_ts`
#include "rosidl_runtime_c/string_functions.h"

bool
dexter_msgs__srv__AddItem_Request__init(dexter_msgs__srv__AddItem_Request * msg)
{
  if (!msg) {
    return false;
  }
  // item_name
  if (!rosidl_runtime_c__String__init(&msg->item_name)) {
    dexter_msgs__srv__AddItem_Request__fini(msg);
    return false;
  }
  // slot
  // expiry_ts
  if (!rosidl_runtime_c__String__init(&msg->expiry_ts)) {
    dexter_msgs__srv__AddItem_Request__fini(msg);
    return false;
  }
  return true;
}

void
dexter_msgs__srv__AddItem_Request__fini(dexter_msgs__srv__AddItem_Request * msg)
{
  if (!msg) {
    return;
  }
  // item_name
  rosidl_runtime_c__String__fini(&msg->item_name);
  // slot
  // expiry_ts
  rosidl_runtime_c__String__fini(&msg->expiry_ts);
}

bool
dexter_msgs__srv__AddItem_Request__are_equal(const dexter_msgs__srv__AddItem_Request * lhs, const dexter_msgs__srv__AddItem_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // item_name
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->item_name), &(rhs->item_name)))
  {
    return false;
  }
  // slot
  if (lhs->slot != rhs->slot) {
    return false;
  }
  // expiry_ts
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->expiry_ts), &(rhs->expiry_ts)))
  {
    return false;
  }
  return true;
}

bool
dexter_msgs__srv__AddItem_Request__copy(
  const dexter_msgs__srv__AddItem_Request * input,
  dexter_msgs__srv__AddItem_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // item_name
  if (!rosidl_runtime_c__String__copy(
      &(input->item_name), &(output->item_name)))
  {
    return false;
  }
  // slot
  output->slot = input->slot;
  // expiry_ts
  if (!rosidl_runtime_c__String__copy(
      &(input->expiry_ts), &(output->expiry_ts)))
  {
    return false;
  }
  return true;
}

dexter_msgs__srv__AddItem_Request *
dexter_msgs__srv__AddItem_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__srv__AddItem_Request * msg = (dexter_msgs__srv__AddItem_Request *)allocator.allocate(sizeof(dexter_msgs__srv__AddItem_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__srv__AddItem_Request));
  bool success = dexter_msgs__srv__AddItem_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__srv__AddItem_Request__destroy(dexter_msgs__srv__AddItem_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__srv__AddItem_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__srv__AddItem_Request__Sequence__init(dexter_msgs__srv__AddItem_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__srv__AddItem_Request * data = NULL;

  if (size) {
    data = (dexter_msgs__srv__AddItem_Request *)allocator.zero_allocate(size, sizeof(dexter_msgs__srv__AddItem_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__srv__AddItem_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__srv__AddItem_Request__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
dexter_msgs__srv__AddItem_Request__Sequence__fini(dexter_msgs__srv__AddItem_Request__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      dexter_msgs__srv__AddItem_Request__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

dexter_msgs__srv__AddItem_Request__Sequence *
dexter_msgs__srv__AddItem_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__srv__AddItem_Request__Sequence * array = (dexter_msgs__srv__AddItem_Request__Sequence *)allocator.allocate(sizeof(dexter_msgs__srv__AddItem_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__srv__AddItem_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__srv__AddItem_Request__Sequence__destroy(dexter_msgs__srv__AddItem_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__srv__AddItem_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__srv__AddItem_Request__Sequence__are_equal(const dexter_msgs__srv__AddItem_Request__Sequence * lhs, const dexter_msgs__srv__AddItem_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__srv__AddItem_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__srv__AddItem_Request__Sequence__copy(
  const dexter_msgs__srv__AddItem_Request__Sequence * input,
  dexter_msgs__srv__AddItem_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__srv__AddItem_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__srv__AddItem_Request * data =
      (dexter_msgs__srv__AddItem_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__srv__AddItem_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__srv__AddItem_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__srv__AddItem_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `item_id`
// Member `message`
// already included above
// #include "rosidl_runtime_c/string_functions.h"

bool
dexter_msgs__srv__AddItem_Response__init(dexter_msgs__srv__AddItem_Response * msg)
{
  if (!msg) {
    return false;
  }
  // success
  // item_id
  if (!rosidl_runtime_c__String__init(&msg->item_id)) {
    dexter_msgs__srv__AddItem_Response__fini(msg);
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    dexter_msgs__srv__AddItem_Response__fini(msg);
    return false;
  }
  return true;
}

void
dexter_msgs__srv__AddItem_Response__fini(dexter_msgs__srv__AddItem_Response * msg)
{
  if (!msg) {
    return;
  }
  // success
  // item_id
  rosidl_runtime_c__String__fini(&msg->item_id);
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
dexter_msgs__srv__AddItem_Response__are_equal(const dexter_msgs__srv__AddItem_Response * lhs, const dexter_msgs__srv__AddItem_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  // item_id
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->item_id), &(rhs->item_id)))
  {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->message), &(rhs->message)))
  {
    return false;
  }
  return true;
}

bool
dexter_msgs__srv__AddItem_Response__copy(
  const dexter_msgs__srv__AddItem_Response * input,
  dexter_msgs__srv__AddItem_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  // item_id
  if (!rosidl_runtime_c__String__copy(
      &(input->item_id), &(output->item_id)))
  {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

dexter_msgs__srv__AddItem_Response *
dexter_msgs__srv__AddItem_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__srv__AddItem_Response * msg = (dexter_msgs__srv__AddItem_Response *)allocator.allocate(sizeof(dexter_msgs__srv__AddItem_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__srv__AddItem_Response));
  bool success = dexter_msgs__srv__AddItem_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__srv__AddItem_Response__destroy(dexter_msgs__srv__AddItem_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__srv__AddItem_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__srv__AddItem_Response__Sequence__init(dexter_msgs__srv__AddItem_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__srv__AddItem_Response * data = NULL;

  if (size) {
    data = (dexter_msgs__srv__AddItem_Response *)allocator.zero_allocate(size, sizeof(dexter_msgs__srv__AddItem_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__srv__AddItem_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__srv__AddItem_Response__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
dexter_msgs__srv__AddItem_Response__Sequence__fini(dexter_msgs__srv__AddItem_Response__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      dexter_msgs__srv__AddItem_Response__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

dexter_msgs__srv__AddItem_Response__Sequence *
dexter_msgs__srv__AddItem_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__srv__AddItem_Response__Sequence * array = (dexter_msgs__srv__AddItem_Response__Sequence *)allocator.allocate(sizeof(dexter_msgs__srv__AddItem_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__srv__AddItem_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__srv__AddItem_Response__Sequence__destroy(dexter_msgs__srv__AddItem_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__srv__AddItem_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__srv__AddItem_Response__Sequence__are_equal(const dexter_msgs__srv__AddItem_Response__Sequence * lhs, const dexter_msgs__srv__AddItem_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__srv__AddItem_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__srv__AddItem_Response__Sequence__copy(
  const dexter_msgs__srv__AddItem_Response__Sequence * input,
  dexter_msgs__srv__AddItem_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__srv__AddItem_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__srv__AddItem_Response * data =
      (dexter_msgs__srv__AddItem_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__srv__AddItem_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__srv__AddItem_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__srv__AddItem_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `info`
#include "service_msgs/msg/detail/service_event_info__functions.h"
// Member `request`
// Member `response`
// already included above
// #include "dexter_msgs/srv/detail/add_item__functions.h"

bool
dexter_msgs__srv__AddItem_Event__init(dexter_msgs__srv__AddItem_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    dexter_msgs__srv__AddItem_Event__fini(msg);
    return false;
  }
  // request
  if (!dexter_msgs__srv__AddItem_Request__Sequence__init(&msg->request, 0)) {
    dexter_msgs__srv__AddItem_Event__fini(msg);
    return false;
  }
  // response
  if (!dexter_msgs__srv__AddItem_Response__Sequence__init(&msg->response, 0)) {
    dexter_msgs__srv__AddItem_Event__fini(msg);
    return false;
  }
  return true;
}

void
dexter_msgs__srv__AddItem_Event__fini(dexter_msgs__srv__AddItem_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  dexter_msgs__srv__AddItem_Request__Sequence__fini(&msg->request);
  // response
  dexter_msgs__srv__AddItem_Response__Sequence__fini(&msg->response);
}

bool
dexter_msgs__srv__AddItem_Event__are_equal(const dexter_msgs__srv__AddItem_Event * lhs, const dexter_msgs__srv__AddItem_Event * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__are_equal(
      &(lhs->info), &(rhs->info)))
  {
    return false;
  }
  // request
  if (!dexter_msgs__srv__AddItem_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!dexter_msgs__srv__AddItem_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
dexter_msgs__srv__AddItem_Event__copy(
  const dexter_msgs__srv__AddItem_Event * input,
  dexter_msgs__srv__AddItem_Event * output)
{
  if (!input || !output) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__copy(
      &(input->info), &(output->info)))
  {
    return false;
  }
  // request
  if (!dexter_msgs__srv__AddItem_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!dexter_msgs__srv__AddItem_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

dexter_msgs__srv__AddItem_Event *
dexter_msgs__srv__AddItem_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__srv__AddItem_Event * msg = (dexter_msgs__srv__AddItem_Event *)allocator.allocate(sizeof(dexter_msgs__srv__AddItem_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__srv__AddItem_Event));
  bool success = dexter_msgs__srv__AddItem_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__srv__AddItem_Event__destroy(dexter_msgs__srv__AddItem_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__srv__AddItem_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__srv__AddItem_Event__Sequence__init(dexter_msgs__srv__AddItem_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__srv__AddItem_Event * data = NULL;

  if (size) {
    data = (dexter_msgs__srv__AddItem_Event *)allocator.zero_allocate(size, sizeof(dexter_msgs__srv__AddItem_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__srv__AddItem_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__srv__AddItem_Event__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
dexter_msgs__srv__AddItem_Event__Sequence__fini(dexter_msgs__srv__AddItem_Event__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      dexter_msgs__srv__AddItem_Event__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

dexter_msgs__srv__AddItem_Event__Sequence *
dexter_msgs__srv__AddItem_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__srv__AddItem_Event__Sequence * array = (dexter_msgs__srv__AddItem_Event__Sequence *)allocator.allocate(sizeof(dexter_msgs__srv__AddItem_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__srv__AddItem_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__srv__AddItem_Event__Sequence__destroy(dexter_msgs__srv__AddItem_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__srv__AddItem_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__srv__AddItem_Event__Sequence__are_equal(const dexter_msgs__srv__AddItem_Event__Sequence * lhs, const dexter_msgs__srv__AddItem_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__srv__AddItem_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__srv__AddItem_Event__Sequence__copy(
  const dexter_msgs__srv__AddItem_Event__Sequence * input,
  dexter_msgs__srv__AddItem_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__srv__AddItem_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__srv__AddItem_Event * data =
      (dexter_msgs__srv__AddItem_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__srv__AddItem_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__srv__AddItem_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__srv__AddItem_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
