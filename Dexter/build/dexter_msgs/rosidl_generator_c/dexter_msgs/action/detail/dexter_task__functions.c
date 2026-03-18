// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from dexter_msgs:action/DexterTask.idl
// generated code does not contain a copyright notice
#include "dexter_msgs/action/detail/dexter_task__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
dexter_msgs__action__DexterTask_Goal__init(dexter_msgs__action__DexterTask_Goal * msg)
{
  if (!msg) {
    return false;
  }
  // task_number
  return true;
}

void
dexter_msgs__action__DexterTask_Goal__fini(dexter_msgs__action__DexterTask_Goal * msg)
{
  if (!msg) {
    return;
  }
  // task_number
}

bool
dexter_msgs__action__DexterTask_Goal__are_equal(const dexter_msgs__action__DexterTask_Goal * lhs, const dexter_msgs__action__DexterTask_Goal * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // task_number
  if (lhs->task_number != rhs->task_number) {
    return false;
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_Goal__copy(
  const dexter_msgs__action__DexterTask_Goal * input,
  dexter_msgs__action__DexterTask_Goal * output)
{
  if (!input || !output) {
    return false;
  }
  // task_number
  output->task_number = input->task_number;
  return true;
}

dexter_msgs__action__DexterTask_Goal *
dexter_msgs__action__DexterTask_Goal__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_Goal * msg = (dexter_msgs__action__DexterTask_Goal *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_Goal), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__action__DexterTask_Goal));
  bool success = dexter_msgs__action__DexterTask_Goal__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__action__DexterTask_Goal__destroy(dexter_msgs__action__DexterTask_Goal * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__action__DexterTask_Goal__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__action__DexterTask_Goal__Sequence__init(dexter_msgs__action__DexterTask_Goal__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_Goal * data = NULL;

  if (size) {
    data = (dexter_msgs__action__DexterTask_Goal *)allocator.zero_allocate(size, sizeof(dexter_msgs__action__DexterTask_Goal), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__action__DexterTask_Goal__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__action__DexterTask_Goal__fini(&data[i - 1]);
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
dexter_msgs__action__DexterTask_Goal__Sequence__fini(dexter_msgs__action__DexterTask_Goal__Sequence * array)
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
      dexter_msgs__action__DexterTask_Goal__fini(&array->data[i]);
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

dexter_msgs__action__DexterTask_Goal__Sequence *
dexter_msgs__action__DexterTask_Goal__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_Goal__Sequence * array = (dexter_msgs__action__DexterTask_Goal__Sequence *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_Goal__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__action__DexterTask_Goal__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__action__DexterTask_Goal__Sequence__destroy(dexter_msgs__action__DexterTask_Goal__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__action__DexterTask_Goal__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__action__DexterTask_Goal__Sequence__are_equal(const dexter_msgs__action__DexterTask_Goal__Sequence * lhs, const dexter_msgs__action__DexterTask_Goal__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__action__DexterTask_Goal__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_Goal__Sequence__copy(
  const dexter_msgs__action__DexterTask_Goal__Sequence * input,
  dexter_msgs__action__DexterTask_Goal__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__action__DexterTask_Goal);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__action__DexterTask_Goal * data =
      (dexter_msgs__action__DexterTask_Goal *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__action__DexterTask_Goal__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__action__DexterTask_Goal__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__action__DexterTask_Goal__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


bool
dexter_msgs__action__DexterTask_Result__init(dexter_msgs__action__DexterTask_Result * msg)
{
  if (!msg) {
    return false;
  }
  // success
  return true;
}

void
dexter_msgs__action__DexterTask_Result__fini(dexter_msgs__action__DexterTask_Result * msg)
{
  if (!msg) {
    return;
  }
  // success
}

bool
dexter_msgs__action__DexterTask_Result__are_equal(const dexter_msgs__action__DexterTask_Result * lhs, const dexter_msgs__action__DexterTask_Result * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_Result__copy(
  const dexter_msgs__action__DexterTask_Result * input,
  dexter_msgs__action__DexterTask_Result * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  return true;
}

dexter_msgs__action__DexterTask_Result *
dexter_msgs__action__DexterTask_Result__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_Result * msg = (dexter_msgs__action__DexterTask_Result *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_Result), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__action__DexterTask_Result));
  bool success = dexter_msgs__action__DexterTask_Result__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__action__DexterTask_Result__destroy(dexter_msgs__action__DexterTask_Result * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__action__DexterTask_Result__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__action__DexterTask_Result__Sequence__init(dexter_msgs__action__DexterTask_Result__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_Result * data = NULL;

  if (size) {
    data = (dexter_msgs__action__DexterTask_Result *)allocator.zero_allocate(size, sizeof(dexter_msgs__action__DexterTask_Result), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__action__DexterTask_Result__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__action__DexterTask_Result__fini(&data[i - 1]);
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
dexter_msgs__action__DexterTask_Result__Sequence__fini(dexter_msgs__action__DexterTask_Result__Sequence * array)
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
      dexter_msgs__action__DexterTask_Result__fini(&array->data[i]);
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

dexter_msgs__action__DexterTask_Result__Sequence *
dexter_msgs__action__DexterTask_Result__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_Result__Sequence * array = (dexter_msgs__action__DexterTask_Result__Sequence *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_Result__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__action__DexterTask_Result__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__action__DexterTask_Result__Sequence__destroy(dexter_msgs__action__DexterTask_Result__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__action__DexterTask_Result__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__action__DexterTask_Result__Sequence__are_equal(const dexter_msgs__action__DexterTask_Result__Sequence * lhs, const dexter_msgs__action__DexterTask_Result__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__action__DexterTask_Result__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_Result__Sequence__copy(
  const dexter_msgs__action__DexterTask_Result__Sequence * input,
  dexter_msgs__action__DexterTask_Result__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__action__DexterTask_Result);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__action__DexterTask_Result * data =
      (dexter_msgs__action__DexterTask_Result *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__action__DexterTask_Result__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__action__DexterTask_Result__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__action__DexterTask_Result__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


bool
dexter_msgs__action__DexterTask_Feedback__init(dexter_msgs__action__DexterTask_Feedback * msg)
{
  if (!msg) {
    return false;
  }
  // percentage
  return true;
}

void
dexter_msgs__action__DexterTask_Feedback__fini(dexter_msgs__action__DexterTask_Feedback * msg)
{
  if (!msg) {
    return;
  }
  // percentage
}

bool
dexter_msgs__action__DexterTask_Feedback__are_equal(const dexter_msgs__action__DexterTask_Feedback * lhs, const dexter_msgs__action__DexterTask_Feedback * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // percentage
  if (lhs->percentage != rhs->percentage) {
    return false;
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_Feedback__copy(
  const dexter_msgs__action__DexterTask_Feedback * input,
  dexter_msgs__action__DexterTask_Feedback * output)
{
  if (!input || !output) {
    return false;
  }
  // percentage
  output->percentage = input->percentage;
  return true;
}

dexter_msgs__action__DexterTask_Feedback *
dexter_msgs__action__DexterTask_Feedback__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_Feedback * msg = (dexter_msgs__action__DexterTask_Feedback *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_Feedback), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__action__DexterTask_Feedback));
  bool success = dexter_msgs__action__DexterTask_Feedback__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__action__DexterTask_Feedback__destroy(dexter_msgs__action__DexterTask_Feedback * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__action__DexterTask_Feedback__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__action__DexterTask_Feedback__Sequence__init(dexter_msgs__action__DexterTask_Feedback__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_Feedback * data = NULL;

  if (size) {
    data = (dexter_msgs__action__DexterTask_Feedback *)allocator.zero_allocate(size, sizeof(dexter_msgs__action__DexterTask_Feedback), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__action__DexterTask_Feedback__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__action__DexterTask_Feedback__fini(&data[i - 1]);
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
dexter_msgs__action__DexterTask_Feedback__Sequence__fini(dexter_msgs__action__DexterTask_Feedback__Sequence * array)
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
      dexter_msgs__action__DexterTask_Feedback__fini(&array->data[i]);
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

dexter_msgs__action__DexterTask_Feedback__Sequence *
dexter_msgs__action__DexterTask_Feedback__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_Feedback__Sequence * array = (dexter_msgs__action__DexterTask_Feedback__Sequence *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_Feedback__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__action__DexterTask_Feedback__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__action__DexterTask_Feedback__Sequence__destroy(dexter_msgs__action__DexterTask_Feedback__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__action__DexterTask_Feedback__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__action__DexterTask_Feedback__Sequence__are_equal(const dexter_msgs__action__DexterTask_Feedback__Sequence * lhs, const dexter_msgs__action__DexterTask_Feedback__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__action__DexterTask_Feedback__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_Feedback__Sequence__copy(
  const dexter_msgs__action__DexterTask_Feedback__Sequence * input,
  dexter_msgs__action__DexterTask_Feedback__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__action__DexterTask_Feedback);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__action__DexterTask_Feedback * data =
      (dexter_msgs__action__DexterTask_Feedback *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__action__DexterTask_Feedback__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__action__DexterTask_Feedback__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__action__DexterTask_Feedback__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
#include "unique_identifier_msgs/msg/detail/uuid__functions.h"
// Member `goal`
// already included above
// #include "dexter_msgs/action/detail/dexter_task__functions.h"

bool
dexter_msgs__action__DexterTask_SendGoal_Request__init(dexter_msgs__action__DexterTask_SendGoal_Request * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    dexter_msgs__action__DexterTask_SendGoal_Request__fini(msg);
    return false;
  }
  // goal
  if (!dexter_msgs__action__DexterTask_Goal__init(&msg->goal)) {
    dexter_msgs__action__DexterTask_SendGoal_Request__fini(msg);
    return false;
  }
  return true;
}

void
dexter_msgs__action__DexterTask_SendGoal_Request__fini(dexter_msgs__action__DexterTask_SendGoal_Request * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
  // goal
  dexter_msgs__action__DexterTask_Goal__fini(&msg->goal);
}

bool
dexter_msgs__action__DexterTask_SendGoal_Request__are_equal(const dexter_msgs__action__DexterTask_SendGoal_Request * lhs, const dexter_msgs__action__DexterTask_SendGoal_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  // goal
  if (!dexter_msgs__action__DexterTask_Goal__are_equal(
      &(lhs->goal), &(rhs->goal)))
  {
    return false;
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_SendGoal_Request__copy(
  const dexter_msgs__action__DexterTask_SendGoal_Request * input,
  dexter_msgs__action__DexterTask_SendGoal_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  // goal
  if (!dexter_msgs__action__DexterTask_Goal__copy(
      &(input->goal), &(output->goal)))
  {
    return false;
  }
  return true;
}

dexter_msgs__action__DexterTask_SendGoal_Request *
dexter_msgs__action__DexterTask_SendGoal_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_SendGoal_Request * msg = (dexter_msgs__action__DexterTask_SendGoal_Request *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_SendGoal_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__action__DexterTask_SendGoal_Request));
  bool success = dexter_msgs__action__DexterTask_SendGoal_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__action__DexterTask_SendGoal_Request__destroy(dexter_msgs__action__DexterTask_SendGoal_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__action__DexterTask_SendGoal_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__init(dexter_msgs__action__DexterTask_SendGoal_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_SendGoal_Request * data = NULL;

  if (size) {
    data = (dexter_msgs__action__DexterTask_SendGoal_Request *)allocator.zero_allocate(size, sizeof(dexter_msgs__action__DexterTask_SendGoal_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__action__DexterTask_SendGoal_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__action__DexterTask_SendGoal_Request__fini(&data[i - 1]);
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
dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__fini(dexter_msgs__action__DexterTask_SendGoal_Request__Sequence * array)
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
      dexter_msgs__action__DexterTask_SendGoal_Request__fini(&array->data[i]);
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

dexter_msgs__action__DexterTask_SendGoal_Request__Sequence *
dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_SendGoal_Request__Sequence * array = (dexter_msgs__action__DexterTask_SendGoal_Request__Sequence *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_SendGoal_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__destroy(dexter_msgs__action__DexterTask_SendGoal_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__are_equal(const dexter_msgs__action__DexterTask_SendGoal_Request__Sequence * lhs, const dexter_msgs__action__DexterTask_SendGoal_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__action__DexterTask_SendGoal_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__copy(
  const dexter_msgs__action__DexterTask_SendGoal_Request__Sequence * input,
  dexter_msgs__action__DexterTask_SendGoal_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__action__DexterTask_SendGoal_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__action__DexterTask_SendGoal_Request * data =
      (dexter_msgs__action__DexterTask_SendGoal_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__action__DexterTask_SendGoal_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__action__DexterTask_SendGoal_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__action__DexterTask_SendGoal_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `stamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
dexter_msgs__action__DexterTask_SendGoal_Response__init(dexter_msgs__action__DexterTask_SendGoal_Response * msg)
{
  if (!msg) {
    return false;
  }
  // accepted
  // stamp
  if (!builtin_interfaces__msg__Time__init(&msg->stamp)) {
    dexter_msgs__action__DexterTask_SendGoal_Response__fini(msg);
    return false;
  }
  return true;
}

void
dexter_msgs__action__DexterTask_SendGoal_Response__fini(dexter_msgs__action__DexterTask_SendGoal_Response * msg)
{
  if (!msg) {
    return;
  }
  // accepted
  // stamp
  builtin_interfaces__msg__Time__fini(&msg->stamp);
}

bool
dexter_msgs__action__DexterTask_SendGoal_Response__are_equal(const dexter_msgs__action__DexterTask_SendGoal_Response * lhs, const dexter_msgs__action__DexterTask_SendGoal_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // accepted
  if (lhs->accepted != rhs->accepted) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__are_equal(
      &(lhs->stamp), &(rhs->stamp)))
  {
    return false;
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_SendGoal_Response__copy(
  const dexter_msgs__action__DexterTask_SendGoal_Response * input,
  dexter_msgs__action__DexterTask_SendGoal_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // accepted
  output->accepted = input->accepted;
  // stamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->stamp), &(output->stamp)))
  {
    return false;
  }
  return true;
}

dexter_msgs__action__DexterTask_SendGoal_Response *
dexter_msgs__action__DexterTask_SendGoal_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_SendGoal_Response * msg = (dexter_msgs__action__DexterTask_SendGoal_Response *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_SendGoal_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__action__DexterTask_SendGoal_Response));
  bool success = dexter_msgs__action__DexterTask_SendGoal_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__action__DexterTask_SendGoal_Response__destroy(dexter_msgs__action__DexterTask_SendGoal_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__action__DexterTask_SendGoal_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__init(dexter_msgs__action__DexterTask_SendGoal_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_SendGoal_Response * data = NULL;

  if (size) {
    data = (dexter_msgs__action__DexterTask_SendGoal_Response *)allocator.zero_allocate(size, sizeof(dexter_msgs__action__DexterTask_SendGoal_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__action__DexterTask_SendGoal_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__action__DexterTask_SendGoal_Response__fini(&data[i - 1]);
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
dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__fini(dexter_msgs__action__DexterTask_SendGoal_Response__Sequence * array)
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
      dexter_msgs__action__DexterTask_SendGoal_Response__fini(&array->data[i]);
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

dexter_msgs__action__DexterTask_SendGoal_Response__Sequence *
dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_SendGoal_Response__Sequence * array = (dexter_msgs__action__DexterTask_SendGoal_Response__Sequence *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_SendGoal_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__destroy(dexter_msgs__action__DexterTask_SendGoal_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__are_equal(const dexter_msgs__action__DexterTask_SendGoal_Response__Sequence * lhs, const dexter_msgs__action__DexterTask_SendGoal_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__action__DexterTask_SendGoal_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__copy(
  const dexter_msgs__action__DexterTask_SendGoal_Response__Sequence * input,
  dexter_msgs__action__DexterTask_SendGoal_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__action__DexterTask_SendGoal_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__action__DexterTask_SendGoal_Response * data =
      (dexter_msgs__action__DexterTask_SendGoal_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__action__DexterTask_SendGoal_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__action__DexterTask_SendGoal_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__action__DexterTask_SendGoal_Response__copy(
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
// #include "dexter_msgs/action/detail/dexter_task__functions.h"

bool
dexter_msgs__action__DexterTask_SendGoal_Event__init(dexter_msgs__action__DexterTask_SendGoal_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    dexter_msgs__action__DexterTask_SendGoal_Event__fini(msg);
    return false;
  }
  // request
  if (!dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__init(&msg->request, 0)) {
    dexter_msgs__action__DexterTask_SendGoal_Event__fini(msg);
    return false;
  }
  // response
  if (!dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__init(&msg->response, 0)) {
    dexter_msgs__action__DexterTask_SendGoal_Event__fini(msg);
    return false;
  }
  return true;
}

void
dexter_msgs__action__DexterTask_SendGoal_Event__fini(dexter_msgs__action__DexterTask_SendGoal_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__fini(&msg->request);
  // response
  dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__fini(&msg->response);
}

bool
dexter_msgs__action__DexterTask_SendGoal_Event__are_equal(const dexter_msgs__action__DexterTask_SendGoal_Event * lhs, const dexter_msgs__action__DexterTask_SendGoal_Event * rhs)
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
  if (!dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_SendGoal_Event__copy(
  const dexter_msgs__action__DexterTask_SendGoal_Event * input,
  dexter_msgs__action__DexterTask_SendGoal_Event * output)
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
  if (!dexter_msgs__action__DexterTask_SendGoal_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!dexter_msgs__action__DexterTask_SendGoal_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

dexter_msgs__action__DexterTask_SendGoal_Event *
dexter_msgs__action__DexterTask_SendGoal_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_SendGoal_Event * msg = (dexter_msgs__action__DexterTask_SendGoal_Event *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_SendGoal_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__action__DexterTask_SendGoal_Event));
  bool success = dexter_msgs__action__DexterTask_SendGoal_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__action__DexterTask_SendGoal_Event__destroy(dexter_msgs__action__DexterTask_SendGoal_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__action__DexterTask_SendGoal_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__action__DexterTask_SendGoal_Event__Sequence__init(dexter_msgs__action__DexterTask_SendGoal_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_SendGoal_Event * data = NULL;

  if (size) {
    data = (dexter_msgs__action__DexterTask_SendGoal_Event *)allocator.zero_allocate(size, sizeof(dexter_msgs__action__DexterTask_SendGoal_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__action__DexterTask_SendGoal_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__action__DexterTask_SendGoal_Event__fini(&data[i - 1]);
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
dexter_msgs__action__DexterTask_SendGoal_Event__Sequence__fini(dexter_msgs__action__DexterTask_SendGoal_Event__Sequence * array)
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
      dexter_msgs__action__DexterTask_SendGoal_Event__fini(&array->data[i]);
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

dexter_msgs__action__DexterTask_SendGoal_Event__Sequence *
dexter_msgs__action__DexterTask_SendGoal_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_SendGoal_Event__Sequence * array = (dexter_msgs__action__DexterTask_SendGoal_Event__Sequence *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_SendGoal_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__action__DexterTask_SendGoal_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__action__DexterTask_SendGoal_Event__Sequence__destroy(dexter_msgs__action__DexterTask_SendGoal_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__action__DexterTask_SendGoal_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__action__DexterTask_SendGoal_Event__Sequence__are_equal(const dexter_msgs__action__DexterTask_SendGoal_Event__Sequence * lhs, const dexter_msgs__action__DexterTask_SendGoal_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__action__DexterTask_SendGoal_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_SendGoal_Event__Sequence__copy(
  const dexter_msgs__action__DexterTask_SendGoal_Event__Sequence * input,
  dexter_msgs__action__DexterTask_SendGoal_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__action__DexterTask_SendGoal_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__action__DexterTask_SendGoal_Event * data =
      (dexter_msgs__action__DexterTask_SendGoal_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__action__DexterTask_SendGoal_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__action__DexterTask_SendGoal_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__action__DexterTask_SendGoal_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__functions.h"

bool
dexter_msgs__action__DexterTask_GetResult_Request__init(dexter_msgs__action__DexterTask_GetResult_Request * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    dexter_msgs__action__DexterTask_GetResult_Request__fini(msg);
    return false;
  }
  return true;
}

void
dexter_msgs__action__DexterTask_GetResult_Request__fini(dexter_msgs__action__DexterTask_GetResult_Request * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
}

bool
dexter_msgs__action__DexterTask_GetResult_Request__are_equal(const dexter_msgs__action__DexterTask_GetResult_Request * lhs, const dexter_msgs__action__DexterTask_GetResult_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_GetResult_Request__copy(
  const dexter_msgs__action__DexterTask_GetResult_Request * input,
  dexter_msgs__action__DexterTask_GetResult_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  return true;
}

dexter_msgs__action__DexterTask_GetResult_Request *
dexter_msgs__action__DexterTask_GetResult_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_GetResult_Request * msg = (dexter_msgs__action__DexterTask_GetResult_Request *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_GetResult_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__action__DexterTask_GetResult_Request));
  bool success = dexter_msgs__action__DexterTask_GetResult_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__action__DexterTask_GetResult_Request__destroy(dexter_msgs__action__DexterTask_GetResult_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__action__DexterTask_GetResult_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__action__DexterTask_GetResult_Request__Sequence__init(dexter_msgs__action__DexterTask_GetResult_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_GetResult_Request * data = NULL;

  if (size) {
    data = (dexter_msgs__action__DexterTask_GetResult_Request *)allocator.zero_allocate(size, sizeof(dexter_msgs__action__DexterTask_GetResult_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__action__DexterTask_GetResult_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__action__DexterTask_GetResult_Request__fini(&data[i - 1]);
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
dexter_msgs__action__DexterTask_GetResult_Request__Sequence__fini(dexter_msgs__action__DexterTask_GetResult_Request__Sequence * array)
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
      dexter_msgs__action__DexterTask_GetResult_Request__fini(&array->data[i]);
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

dexter_msgs__action__DexterTask_GetResult_Request__Sequence *
dexter_msgs__action__DexterTask_GetResult_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_GetResult_Request__Sequence * array = (dexter_msgs__action__DexterTask_GetResult_Request__Sequence *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_GetResult_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__action__DexterTask_GetResult_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__action__DexterTask_GetResult_Request__Sequence__destroy(dexter_msgs__action__DexterTask_GetResult_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__action__DexterTask_GetResult_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__action__DexterTask_GetResult_Request__Sequence__are_equal(const dexter_msgs__action__DexterTask_GetResult_Request__Sequence * lhs, const dexter_msgs__action__DexterTask_GetResult_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__action__DexterTask_GetResult_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_GetResult_Request__Sequence__copy(
  const dexter_msgs__action__DexterTask_GetResult_Request__Sequence * input,
  dexter_msgs__action__DexterTask_GetResult_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__action__DexterTask_GetResult_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__action__DexterTask_GetResult_Request * data =
      (dexter_msgs__action__DexterTask_GetResult_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__action__DexterTask_GetResult_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__action__DexterTask_GetResult_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__action__DexterTask_GetResult_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `result`
// already included above
// #include "dexter_msgs/action/detail/dexter_task__functions.h"

bool
dexter_msgs__action__DexterTask_GetResult_Response__init(dexter_msgs__action__DexterTask_GetResult_Response * msg)
{
  if (!msg) {
    return false;
  }
  // status
  // result
  if (!dexter_msgs__action__DexterTask_Result__init(&msg->result)) {
    dexter_msgs__action__DexterTask_GetResult_Response__fini(msg);
    return false;
  }
  return true;
}

void
dexter_msgs__action__DexterTask_GetResult_Response__fini(dexter_msgs__action__DexterTask_GetResult_Response * msg)
{
  if (!msg) {
    return;
  }
  // status
  // result
  dexter_msgs__action__DexterTask_Result__fini(&msg->result);
}

bool
dexter_msgs__action__DexterTask_GetResult_Response__are_equal(const dexter_msgs__action__DexterTask_GetResult_Response * lhs, const dexter_msgs__action__DexterTask_GetResult_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // status
  if (lhs->status != rhs->status) {
    return false;
  }
  // result
  if (!dexter_msgs__action__DexterTask_Result__are_equal(
      &(lhs->result), &(rhs->result)))
  {
    return false;
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_GetResult_Response__copy(
  const dexter_msgs__action__DexterTask_GetResult_Response * input,
  dexter_msgs__action__DexterTask_GetResult_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // status
  output->status = input->status;
  // result
  if (!dexter_msgs__action__DexterTask_Result__copy(
      &(input->result), &(output->result)))
  {
    return false;
  }
  return true;
}

dexter_msgs__action__DexterTask_GetResult_Response *
dexter_msgs__action__DexterTask_GetResult_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_GetResult_Response * msg = (dexter_msgs__action__DexterTask_GetResult_Response *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_GetResult_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__action__DexterTask_GetResult_Response));
  bool success = dexter_msgs__action__DexterTask_GetResult_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__action__DexterTask_GetResult_Response__destroy(dexter_msgs__action__DexterTask_GetResult_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__action__DexterTask_GetResult_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__action__DexterTask_GetResult_Response__Sequence__init(dexter_msgs__action__DexterTask_GetResult_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_GetResult_Response * data = NULL;

  if (size) {
    data = (dexter_msgs__action__DexterTask_GetResult_Response *)allocator.zero_allocate(size, sizeof(dexter_msgs__action__DexterTask_GetResult_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__action__DexterTask_GetResult_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__action__DexterTask_GetResult_Response__fini(&data[i - 1]);
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
dexter_msgs__action__DexterTask_GetResult_Response__Sequence__fini(dexter_msgs__action__DexterTask_GetResult_Response__Sequence * array)
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
      dexter_msgs__action__DexterTask_GetResult_Response__fini(&array->data[i]);
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

dexter_msgs__action__DexterTask_GetResult_Response__Sequence *
dexter_msgs__action__DexterTask_GetResult_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_GetResult_Response__Sequence * array = (dexter_msgs__action__DexterTask_GetResult_Response__Sequence *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_GetResult_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__action__DexterTask_GetResult_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__action__DexterTask_GetResult_Response__Sequence__destroy(dexter_msgs__action__DexterTask_GetResult_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__action__DexterTask_GetResult_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__action__DexterTask_GetResult_Response__Sequence__are_equal(const dexter_msgs__action__DexterTask_GetResult_Response__Sequence * lhs, const dexter_msgs__action__DexterTask_GetResult_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__action__DexterTask_GetResult_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_GetResult_Response__Sequence__copy(
  const dexter_msgs__action__DexterTask_GetResult_Response__Sequence * input,
  dexter_msgs__action__DexterTask_GetResult_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__action__DexterTask_GetResult_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__action__DexterTask_GetResult_Response * data =
      (dexter_msgs__action__DexterTask_GetResult_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__action__DexterTask_GetResult_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__action__DexterTask_GetResult_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__action__DexterTask_GetResult_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `info`
// already included above
// #include "service_msgs/msg/detail/service_event_info__functions.h"
// Member `request`
// Member `response`
// already included above
// #include "dexter_msgs/action/detail/dexter_task__functions.h"

bool
dexter_msgs__action__DexterTask_GetResult_Event__init(dexter_msgs__action__DexterTask_GetResult_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    dexter_msgs__action__DexterTask_GetResult_Event__fini(msg);
    return false;
  }
  // request
  if (!dexter_msgs__action__DexterTask_GetResult_Request__Sequence__init(&msg->request, 0)) {
    dexter_msgs__action__DexterTask_GetResult_Event__fini(msg);
    return false;
  }
  // response
  if (!dexter_msgs__action__DexterTask_GetResult_Response__Sequence__init(&msg->response, 0)) {
    dexter_msgs__action__DexterTask_GetResult_Event__fini(msg);
    return false;
  }
  return true;
}

void
dexter_msgs__action__DexterTask_GetResult_Event__fini(dexter_msgs__action__DexterTask_GetResult_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  dexter_msgs__action__DexterTask_GetResult_Request__Sequence__fini(&msg->request);
  // response
  dexter_msgs__action__DexterTask_GetResult_Response__Sequence__fini(&msg->response);
}

bool
dexter_msgs__action__DexterTask_GetResult_Event__are_equal(const dexter_msgs__action__DexterTask_GetResult_Event * lhs, const dexter_msgs__action__DexterTask_GetResult_Event * rhs)
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
  if (!dexter_msgs__action__DexterTask_GetResult_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!dexter_msgs__action__DexterTask_GetResult_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_GetResult_Event__copy(
  const dexter_msgs__action__DexterTask_GetResult_Event * input,
  dexter_msgs__action__DexterTask_GetResult_Event * output)
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
  if (!dexter_msgs__action__DexterTask_GetResult_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!dexter_msgs__action__DexterTask_GetResult_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

dexter_msgs__action__DexterTask_GetResult_Event *
dexter_msgs__action__DexterTask_GetResult_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_GetResult_Event * msg = (dexter_msgs__action__DexterTask_GetResult_Event *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_GetResult_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__action__DexterTask_GetResult_Event));
  bool success = dexter_msgs__action__DexterTask_GetResult_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__action__DexterTask_GetResult_Event__destroy(dexter_msgs__action__DexterTask_GetResult_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__action__DexterTask_GetResult_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__action__DexterTask_GetResult_Event__Sequence__init(dexter_msgs__action__DexterTask_GetResult_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_GetResult_Event * data = NULL;

  if (size) {
    data = (dexter_msgs__action__DexterTask_GetResult_Event *)allocator.zero_allocate(size, sizeof(dexter_msgs__action__DexterTask_GetResult_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__action__DexterTask_GetResult_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__action__DexterTask_GetResult_Event__fini(&data[i - 1]);
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
dexter_msgs__action__DexterTask_GetResult_Event__Sequence__fini(dexter_msgs__action__DexterTask_GetResult_Event__Sequence * array)
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
      dexter_msgs__action__DexterTask_GetResult_Event__fini(&array->data[i]);
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

dexter_msgs__action__DexterTask_GetResult_Event__Sequence *
dexter_msgs__action__DexterTask_GetResult_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_GetResult_Event__Sequence * array = (dexter_msgs__action__DexterTask_GetResult_Event__Sequence *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_GetResult_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__action__DexterTask_GetResult_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__action__DexterTask_GetResult_Event__Sequence__destroy(dexter_msgs__action__DexterTask_GetResult_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__action__DexterTask_GetResult_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__action__DexterTask_GetResult_Event__Sequence__are_equal(const dexter_msgs__action__DexterTask_GetResult_Event__Sequence * lhs, const dexter_msgs__action__DexterTask_GetResult_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__action__DexterTask_GetResult_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_GetResult_Event__Sequence__copy(
  const dexter_msgs__action__DexterTask_GetResult_Event__Sequence * input,
  dexter_msgs__action__DexterTask_GetResult_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__action__DexterTask_GetResult_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__action__DexterTask_GetResult_Event * data =
      (dexter_msgs__action__DexterTask_GetResult_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__action__DexterTask_GetResult_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__action__DexterTask_GetResult_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__action__DexterTask_GetResult_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__functions.h"
// Member `feedback`
// already included above
// #include "dexter_msgs/action/detail/dexter_task__functions.h"

bool
dexter_msgs__action__DexterTask_FeedbackMessage__init(dexter_msgs__action__DexterTask_FeedbackMessage * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    dexter_msgs__action__DexterTask_FeedbackMessage__fini(msg);
    return false;
  }
  // feedback
  if (!dexter_msgs__action__DexterTask_Feedback__init(&msg->feedback)) {
    dexter_msgs__action__DexterTask_FeedbackMessage__fini(msg);
    return false;
  }
  return true;
}

void
dexter_msgs__action__DexterTask_FeedbackMessage__fini(dexter_msgs__action__DexterTask_FeedbackMessage * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
  // feedback
  dexter_msgs__action__DexterTask_Feedback__fini(&msg->feedback);
}

bool
dexter_msgs__action__DexterTask_FeedbackMessage__are_equal(const dexter_msgs__action__DexterTask_FeedbackMessage * lhs, const dexter_msgs__action__DexterTask_FeedbackMessage * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  // feedback
  if (!dexter_msgs__action__DexterTask_Feedback__are_equal(
      &(lhs->feedback), &(rhs->feedback)))
  {
    return false;
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_FeedbackMessage__copy(
  const dexter_msgs__action__DexterTask_FeedbackMessage * input,
  dexter_msgs__action__DexterTask_FeedbackMessage * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  // feedback
  if (!dexter_msgs__action__DexterTask_Feedback__copy(
      &(input->feedback), &(output->feedback)))
  {
    return false;
  }
  return true;
}

dexter_msgs__action__DexterTask_FeedbackMessage *
dexter_msgs__action__DexterTask_FeedbackMessage__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_FeedbackMessage * msg = (dexter_msgs__action__DexterTask_FeedbackMessage *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_FeedbackMessage), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(dexter_msgs__action__DexterTask_FeedbackMessage));
  bool success = dexter_msgs__action__DexterTask_FeedbackMessage__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
dexter_msgs__action__DexterTask_FeedbackMessage__destroy(dexter_msgs__action__DexterTask_FeedbackMessage * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    dexter_msgs__action__DexterTask_FeedbackMessage__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
dexter_msgs__action__DexterTask_FeedbackMessage__Sequence__init(dexter_msgs__action__DexterTask_FeedbackMessage__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_FeedbackMessage * data = NULL;

  if (size) {
    data = (dexter_msgs__action__DexterTask_FeedbackMessage *)allocator.zero_allocate(size, sizeof(dexter_msgs__action__DexterTask_FeedbackMessage), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = dexter_msgs__action__DexterTask_FeedbackMessage__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        dexter_msgs__action__DexterTask_FeedbackMessage__fini(&data[i - 1]);
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
dexter_msgs__action__DexterTask_FeedbackMessage__Sequence__fini(dexter_msgs__action__DexterTask_FeedbackMessage__Sequence * array)
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
      dexter_msgs__action__DexterTask_FeedbackMessage__fini(&array->data[i]);
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

dexter_msgs__action__DexterTask_FeedbackMessage__Sequence *
dexter_msgs__action__DexterTask_FeedbackMessage__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  dexter_msgs__action__DexterTask_FeedbackMessage__Sequence * array = (dexter_msgs__action__DexterTask_FeedbackMessage__Sequence *)allocator.allocate(sizeof(dexter_msgs__action__DexterTask_FeedbackMessage__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = dexter_msgs__action__DexterTask_FeedbackMessage__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
dexter_msgs__action__DexterTask_FeedbackMessage__Sequence__destroy(dexter_msgs__action__DexterTask_FeedbackMessage__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    dexter_msgs__action__DexterTask_FeedbackMessage__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
dexter_msgs__action__DexterTask_FeedbackMessage__Sequence__are_equal(const dexter_msgs__action__DexterTask_FeedbackMessage__Sequence * lhs, const dexter_msgs__action__DexterTask_FeedbackMessage__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!dexter_msgs__action__DexterTask_FeedbackMessage__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
dexter_msgs__action__DexterTask_FeedbackMessage__Sequence__copy(
  const dexter_msgs__action__DexterTask_FeedbackMessage__Sequence * input,
  dexter_msgs__action__DexterTask_FeedbackMessage__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(dexter_msgs__action__DexterTask_FeedbackMessage);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    dexter_msgs__action__DexterTask_FeedbackMessage * data =
      (dexter_msgs__action__DexterTask_FeedbackMessage *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!dexter_msgs__action__DexterTask_FeedbackMessage__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          dexter_msgs__action__DexterTask_FeedbackMessage__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!dexter_msgs__action__DexterTask_FeedbackMessage__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
