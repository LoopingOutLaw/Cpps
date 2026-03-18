// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from dexter_msgs:srv/DispatchItem.idl
// generated code does not contain a copyright notice

#include "dexter_msgs/srv/detail/dispatch_item__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_dexter_msgs
const rosidl_type_hash_t *
dexter_msgs__srv__DispatchItem__get_type_hash(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x48, 0x27, 0x23, 0x55, 0x50, 0x15, 0x83, 0x21,
      0xe5, 0x0a, 0x2d, 0x24, 0x83, 0xdc, 0xb9, 0x41,
      0xc8, 0x49, 0x81, 0xd3, 0xa0, 0x6e, 0x28, 0x9b,
      0x61, 0x04, 0xe3, 0xe2, 0xcd, 0x24, 0x1b, 0x50,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_dexter_msgs
const rosidl_type_hash_t *
dexter_msgs__srv__DispatchItem_Request__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xdc, 0x95, 0x70, 0x14, 0x18, 0xfc, 0xc4, 0x35,
      0x93, 0x15, 0x76, 0xfc, 0x72, 0x2a, 0xc7, 0x48,
      0xd5, 0xd6, 0x80, 0x1a, 0x27, 0x06, 0x88, 0x6a,
      0x1b, 0xf4, 0xcf, 0xdf, 0xdc, 0x2e, 0xf3, 0x80,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_dexter_msgs
const rosidl_type_hash_t *
dexter_msgs__srv__DispatchItem_Response__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x13, 0x14, 0x72, 0xd1, 0xea, 0xc8, 0x50, 0x70,
      0x3a, 0xcf, 0x93, 0x67, 0x7f, 0xde, 0xf2, 0x7f,
      0x67, 0x26, 0x4a, 0x92, 0x8a, 0xe7, 0xe5, 0x35,
      0xc7, 0x35, 0x66, 0xb2, 0x15, 0xd3, 0xcf, 0x0c,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_dexter_msgs
const rosidl_type_hash_t *
dexter_msgs__srv__DispatchItem_Event__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x0f, 0x54, 0xa2, 0x83, 0xbf, 0x86, 0xdd, 0xcc,
      0xb5, 0x6f, 0x86, 0x10, 0xf4, 0x69, 0x52, 0x72,
      0xaa, 0x97, 0x3d, 0x1f, 0x89, 0x9d, 0x0d, 0xaf,
      0x14, 0x38, 0xfc, 0xc5, 0x19, 0x1a, 0xce, 0x97,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "builtin_interfaces/msg/detail/time__functions.h"
#include "service_msgs/msg/detail/service_event_info__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t builtin_interfaces__msg__Time__EXPECTED_HASH = {1, {
    0xb1, 0x06, 0x23, 0x5e, 0x25, 0xa4, 0xc5, 0xed,
    0x35, 0x09, 0x8a, 0xa0, 0xa6, 0x1a, 0x3e, 0xe9,
    0xc9, 0xb1, 0x8d, 0x19, 0x7f, 0x39, 0x8b, 0x0e,
    0x42, 0x06, 0xce, 0xa9, 0xac, 0xf9, 0xc1, 0x97,
  }};
static const rosidl_type_hash_t service_msgs__msg__ServiceEventInfo__EXPECTED_HASH = {1, {
    0x41, 0xbc, 0xbb, 0xe0, 0x7a, 0x75, 0xc9, 0xb5,
    0x2b, 0xc9, 0x6b, 0xfd, 0x5c, 0x24, 0xd7, 0xf0,
    0xfc, 0x0a, 0x08, 0xc0, 0xcb, 0x79, 0x21, 0xb3,
    0x37, 0x3c, 0x57, 0x32, 0x34, 0x5a, 0x6f, 0x45,
  }};
#endif

static char dexter_msgs__srv__DispatchItem__TYPE_NAME[] = "dexter_msgs/srv/DispatchItem";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";
static char dexter_msgs__srv__DispatchItem_Event__TYPE_NAME[] = "dexter_msgs/srv/DispatchItem_Event";
static char dexter_msgs__srv__DispatchItem_Request__TYPE_NAME[] = "dexter_msgs/srv/DispatchItem_Request";
static char dexter_msgs__srv__DispatchItem_Response__TYPE_NAME[] = "dexter_msgs/srv/DispatchItem_Response";
static char service_msgs__msg__ServiceEventInfo__TYPE_NAME[] = "service_msgs/msg/ServiceEventInfo";

// Define type names, field names, and default values
static char dexter_msgs__srv__DispatchItem__FIELD_NAME__request_message[] = "request_message";
static char dexter_msgs__srv__DispatchItem__FIELD_NAME__response_message[] = "response_message";
static char dexter_msgs__srv__DispatchItem__FIELD_NAME__event_message[] = "event_message";

static rosidl_runtime_c__type_description__Field dexter_msgs__srv__DispatchItem__FIELDS[] = {
  {
    {dexter_msgs__srv__DispatchItem__FIELD_NAME__request_message, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {dexter_msgs__srv__DispatchItem_Request__TYPE_NAME, 36, 36},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem__FIELD_NAME__response_message, 16, 16},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {dexter_msgs__srv__DispatchItem_Response__TYPE_NAME, 37, 37},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem__FIELD_NAME__event_message, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {dexter_msgs__srv__DispatchItem_Event__TYPE_NAME, 34, 34},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription dexter_msgs__srv__DispatchItem__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Event__TYPE_NAME, 34, 34},
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Request__TYPE_NAME, 36, 36},
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Response__TYPE_NAME, 37, 37},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
dexter_msgs__srv__DispatchItem__get_type_description(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {dexter_msgs__srv__DispatchItem__TYPE_NAME, 28, 28},
      {dexter_msgs__srv__DispatchItem__FIELDS, 3, 3},
    },
    {dexter_msgs__srv__DispatchItem__REFERENCED_TYPE_DESCRIPTIONS, 5, 5},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = dexter_msgs__srv__DispatchItem_Event__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = dexter_msgs__srv__DispatchItem_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[3].fields = dexter_msgs__srv__DispatchItem_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[4].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char dexter_msgs__srv__DispatchItem_Request__FIELD_NAME__mode[] = "mode";

static rosidl_runtime_c__type_description__Field dexter_msgs__srv__DispatchItem_Request__FIELDS[] = {
  {
    {dexter_msgs__srv__DispatchItem_Request__FIELD_NAME__mode, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
dexter_msgs__srv__DispatchItem_Request__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {dexter_msgs__srv__DispatchItem_Request__TYPE_NAME, 36, 36},
      {dexter_msgs__srv__DispatchItem_Request__FIELDS, 1, 1},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__success[] = "success";
static char dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__item_name[] = "item_name";
static char dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__item_id[] = "item_id";
static char dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__slot_number[] = "slot_number";
static char dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__expiry_date[] = "expiry_date";
static char dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__message[] = "message";

static rosidl_runtime_c__type_description__Field dexter_msgs__srv__DispatchItem_Response__FIELDS[] = {
  {
    {dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__success, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__item_name, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__item_id, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__slot_number, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__expiry_date, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Response__FIELD_NAME__message, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
dexter_msgs__srv__DispatchItem_Response__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {dexter_msgs__srv__DispatchItem_Response__TYPE_NAME, 37, 37},
      {dexter_msgs__srv__DispatchItem_Response__FIELDS, 6, 6},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char dexter_msgs__srv__DispatchItem_Event__FIELD_NAME__info[] = "info";
static char dexter_msgs__srv__DispatchItem_Event__FIELD_NAME__request[] = "request";
static char dexter_msgs__srv__DispatchItem_Event__FIELD_NAME__response[] = "response";

static rosidl_runtime_c__type_description__Field dexter_msgs__srv__DispatchItem_Event__FIELDS[] = {
  {
    {dexter_msgs__srv__DispatchItem_Event__FIELD_NAME__info, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Event__FIELD_NAME__request, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {dexter_msgs__srv__DispatchItem_Request__TYPE_NAME, 36, 36},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Event__FIELD_NAME__response, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {dexter_msgs__srv__DispatchItem_Response__TYPE_NAME, 37, 37},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription dexter_msgs__srv__DispatchItem_Event__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Request__TYPE_NAME, 36, 36},
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__DispatchItem_Response__TYPE_NAME, 37, 37},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
dexter_msgs__srv__DispatchItem_Event__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {dexter_msgs__srv__DispatchItem_Event__TYPE_NAME, 34, 34},
      {dexter_msgs__srv__DispatchItem_Event__FIELDS, 3, 3},
    },
    {dexter_msgs__srv__DispatchItem_Event__REFERENCED_TYPE_DESCRIPTIONS, 4, 4},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = dexter_msgs__srv__DispatchItem_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = dexter_msgs__srv__DispatchItem_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[3].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "string mode        # \"FIFO\" or \"FEFO\"\n"
  "---\n"
  "bool   success\n"
  "string item_name\n"
  "string item_id\n"
  "int32  slot_number\n"
  "string expiry_date\n"
  "string message";

static char srv_encoding[] = "srv";
static char implicit_encoding[] = "implicit";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
dexter_msgs__srv__DispatchItem__get_individual_type_description_source(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {dexter_msgs__srv__DispatchItem__TYPE_NAME, 28, 28},
    {srv_encoding, 3, 3},
    {toplevel_type_raw_source, 142, 142},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
dexter_msgs__srv__DispatchItem_Request__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {dexter_msgs__srv__DispatchItem_Request__TYPE_NAME, 36, 36},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
dexter_msgs__srv__DispatchItem_Response__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {dexter_msgs__srv__DispatchItem_Response__TYPE_NAME, 37, 37},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
dexter_msgs__srv__DispatchItem_Event__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {dexter_msgs__srv__DispatchItem_Event__TYPE_NAME, 34, 34},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
dexter_msgs__srv__DispatchItem__get_type_description_sources(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[6];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 6, 6};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *dexter_msgs__srv__DispatchItem__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *dexter_msgs__srv__DispatchItem_Event__get_individual_type_description_source(NULL);
    sources[3] = *dexter_msgs__srv__DispatchItem_Request__get_individual_type_description_source(NULL);
    sources[4] = *dexter_msgs__srv__DispatchItem_Response__get_individual_type_description_source(NULL);
    sources[5] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
dexter_msgs__srv__DispatchItem_Request__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *dexter_msgs__srv__DispatchItem_Request__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
dexter_msgs__srv__DispatchItem_Response__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *dexter_msgs__srv__DispatchItem_Response__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
dexter_msgs__srv__DispatchItem_Event__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[5];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 5, 5};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *dexter_msgs__srv__DispatchItem_Event__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *dexter_msgs__srv__DispatchItem_Request__get_individual_type_description_source(NULL);
    sources[3] = *dexter_msgs__srv__DispatchItem_Response__get_individual_type_description_source(NULL);
    sources[4] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
