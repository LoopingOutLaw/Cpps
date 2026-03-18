// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from dexter_msgs:srv/AddItem.idl
// generated code does not contain a copyright notice

#include "dexter_msgs/srv/detail/add_item__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_dexter_msgs
const rosidl_type_hash_t *
dexter_msgs__srv__AddItem__get_type_hash(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xc7, 0xa8, 0xca, 0xf8, 0x30, 0x69, 0x8d, 0x00,
      0x5e, 0x5c, 0x32, 0xb2, 0x19, 0x39, 0xc7, 0x43,
      0x98, 0x86, 0xe5, 0xad, 0x37, 0xd6, 0x42, 0x7b,
      0x6d, 0x45, 0xa2, 0xa4, 0x5f, 0x9b, 0x99, 0x88,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_dexter_msgs
const rosidl_type_hash_t *
dexter_msgs__srv__AddItem_Request__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x91, 0x4f, 0x78, 0xbc, 0x5b, 0x89, 0x80, 0x03,
      0x49, 0x54, 0x75, 0xe1, 0x78, 0x4d, 0x7e, 0xf5,
      0x19, 0xc3, 0x49, 0xfc, 0xaf, 0x12, 0xd9, 0x6f,
      0x33, 0xdb, 0x3f, 0x4a, 0x30, 0xe8, 0x48, 0xf5,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_dexter_msgs
const rosidl_type_hash_t *
dexter_msgs__srv__AddItem_Response__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x4d, 0xa2, 0xf1, 0xb9, 0x71, 0x4d, 0x79, 0xd6,
      0xfa, 0xd6, 0x72, 0xd8, 0x0c, 0xab, 0x63, 0x65,
      0x26, 0xbc, 0xc4, 0x50, 0xcd, 0x93, 0xbc, 0x00,
      0xa5, 0x7e, 0xa8, 0x29, 0x37, 0xfb, 0x55, 0x66,
    }};
  return &hash;
}

ROSIDL_GENERATOR_C_PUBLIC_dexter_msgs
const rosidl_type_hash_t *
dexter_msgs__srv__AddItem_Event__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x43, 0x8c, 0xc9, 0xc7, 0xc6, 0x5e, 0xb7, 0xe2,
      0x55, 0x77, 0x9e, 0xcd, 0x69, 0x41, 0xf5, 0xf4,
      0xe3, 0x98, 0xa1, 0xf3, 0x92, 0x3f, 0xf3, 0x1f,
      0xfd, 0x0c, 0x79, 0x32, 0x71, 0xd9, 0x22, 0x4a,
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

static char dexter_msgs__srv__AddItem__TYPE_NAME[] = "dexter_msgs/srv/AddItem";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";
static char dexter_msgs__srv__AddItem_Event__TYPE_NAME[] = "dexter_msgs/srv/AddItem_Event";
static char dexter_msgs__srv__AddItem_Request__TYPE_NAME[] = "dexter_msgs/srv/AddItem_Request";
static char dexter_msgs__srv__AddItem_Response__TYPE_NAME[] = "dexter_msgs/srv/AddItem_Response";
static char service_msgs__msg__ServiceEventInfo__TYPE_NAME[] = "service_msgs/msg/ServiceEventInfo";

// Define type names, field names, and default values
static char dexter_msgs__srv__AddItem__FIELD_NAME__request_message[] = "request_message";
static char dexter_msgs__srv__AddItem__FIELD_NAME__response_message[] = "response_message";
static char dexter_msgs__srv__AddItem__FIELD_NAME__event_message[] = "event_message";

static rosidl_runtime_c__type_description__Field dexter_msgs__srv__AddItem__FIELDS[] = {
  {
    {dexter_msgs__srv__AddItem__FIELD_NAME__request_message, 15, 15},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {dexter_msgs__srv__AddItem_Request__TYPE_NAME, 31, 31},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem__FIELD_NAME__response_message, 16, 16},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {dexter_msgs__srv__AddItem_Response__TYPE_NAME, 32, 32},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem__FIELD_NAME__event_message, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {dexter_msgs__srv__AddItem_Event__TYPE_NAME, 29, 29},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription dexter_msgs__srv__AddItem__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem_Event__TYPE_NAME, 29, 29},
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem_Request__TYPE_NAME, 31, 31},
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem_Response__TYPE_NAME, 32, 32},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
dexter_msgs__srv__AddItem__get_type_description(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {dexter_msgs__srv__AddItem__TYPE_NAME, 23, 23},
      {dexter_msgs__srv__AddItem__FIELDS, 3, 3},
    },
    {dexter_msgs__srv__AddItem__REFERENCED_TYPE_DESCRIPTIONS, 5, 5},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = dexter_msgs__srv__AddItem_Event__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = dexter_msgs__srv__AddItem_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[3].fields = dexter_msgs__srv__AddItem_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[4].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char dexter_msgs__srv__AddItem_Request__FIELD_NAME__item_name[] = "item_name";
static char dexter_msgs__srv__AddItem_Request__FIELD_NAME__slot[] = "slot";
static char dexter_msgs__srv__AddItem_Request__FIELD_NAME__expiry_ts[] = "expiry_ts";

static rosidl_runtime_c__type_description__Field dexter_msgs__srv__AddItem_Request__FIELDS[] = {
  {
    {dexter_msgs__srv__AddItem_Request__FIELD_NAME__item_name, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem_Request__FIELD_NAME__slot, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem_Request__FIELD_NAME__expiry_ts, 9, 9},
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
dexter_msgs__srv__AddItem_Request__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {dexter_msgs__srv__AddItem_Request__TYPE_NAME, 31, 31},
      {dexter_msgs__srv__AddItem_Request__FIELDS, 3, 3},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char dexter_msgs__srv__AddItem_Response__FIELD_NAME__success[] = "success";
static char dexter_msgs__srv__AddItem_Response__FIELD_NAME__item_id[] = "item_id";
static char dexter_msgs__srv__AddItem_Response__FIELD_NAME__message[] = "message";

static rosidl_runtime_c__type_description__Field dexter_msgs__srv__AddItem_Response__FIELDS[] = {
  {
    {dexter_msgs__srv__AddItem_Response__FIELD_NAME__success, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem_Response__FIELD_NAME__item_id, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem_Response__FIELD_NAME__message, 7, 7},
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
dexter_msgs__srv__AddItem_Response__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {dexter_msgs__srv__AddItem_Response__TYPE_NAME, 32, 32},
      {dexter_msgs__srv__AddItem_Response__FIELDS, 3, 3},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}
// Define type names, field names, and default values
static char dexter_msgs__srv__AddItem_Event__FIELD_NAME__info[] = "info";
static char dexter_msgs__srv__AddItem_Event__FIELD_NAME__request[] = "request";
static char dexter_msgs__srv__AddItem_Event__FIELD_NAME__response[] = "response";

static rosidl_runtime_c__type_description__Field dexter_msgs__srv__AddItem_Event__FIELDS[] = {
  {
    {dexter_msgs__srv__AddItem_Event__FIELD_NAME__info, 4, 4},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem_Event__FIELD_NAME__request, 7, 7},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {dexter_msgs__srv__AddItem_Request__TYPE_NAME, 31, 31},
    },
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem_Event__FIELD_NAME__response, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_BOUNDED_SEQUENCE,
      1,
      0,
      {dexter_msgs__srv__AddItem_Response__TYPE_NAME, 32, 32},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription dexter_msgs__srv__AddItem_Event__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem_Request__TYPE_NAME, 31, 31},
    {NULL, 0, 0},
  },
  {
    {dexter_msgs__srv__AddItem_Response__TYPE_NAME, 32, 32},
    {NULL, 0, 0},
  },
  {
    {service_msgs__msg__ServiceEventInfo__TYPE_NAME, 33, 33},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
dexter_msgs__srv__AddItem_Event__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {dexter_msgs__srv__AddItem_Event__TYPE_NAME, 29, 29},
      {dexter_msgs__srv__AddItem_Event__FIELDS, 3, 3},
    },
    {dexter_msgs__srv__AddItem_Event__REFERENCED_TYPE_DESCRIPTIONS, 4, 4},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[1].fields = dexter_msgs__srv__AddItem_Request__get_type_description(NULL)->type_description.fields;
    description.referenced_type_descriptions.data[2].fields = dexter_msgs__srv__AddItem_Response__get_type_description(NULL)->type_description.fields;
    assert(0 == memcmp(&service_msgs__msg__ServiceEventInfo__EXPECTED_HASH, service_msgs__msg__ServiceEventInfo__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[3].fields = service_msgs__msg__ServiceEventInfo__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "string item_name\n"
  "int32  slot\n"
  "string expiry_ts    # Unix timestamp as string; empty = no expiry\n"
  "---\n"
  "bool   success\n"
  "string item_id\n"
  "string message";

static char srv_encoding[] = "srv";
static char implicit_encoding[] = "implicit";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
dexter_msgs__srv__AddItem__get_individual_type_description_source(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {dexter_msgs__srv__AddItem__TYPE_NAME, 23, 23},
    {srv_encoding, 3, 3},
    {toplevel_type_raw_source, 144, 144},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
dexter_msgs__srv__AddItem_Request__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {dexter_msgs__srv__AddItem_Request__TYPE_NAME, 31, 31},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
dexter_msgs__srv__AddItem_Response__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {dexter_msgs__srv__AddItem_Response__TYPE_NAME, 32, 32},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource *
dexter_msgs__srv__AddItem_Event__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {dexter_msgs__srv__AddItem_Event__TYPE_NAME, 29, 29},
    {implicit_encoding, 8, 8},
    {NULL, 0, 0},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
dexter_msgs__srv__AddItem__get_type_description_sources(
  const rosidl_service_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[6];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 6, 6};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *dexter_msgs__srv__AddItem__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *dexter_msgs__srv__AddItem_Event__get_individual_type_description_source(NULL);
    sources[3] = *dexter_msgs__srv__AddItem_Request__get_individual_type_description_source(NULL);
    sources[4] = *dexter_msgs__srv__AddItem_Response__get_individual_type_description_source(NULL);
    sources[5] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
dexter_msgs__srv__AddItem_Request__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *dexter_msgs__srv__AddItem_Request__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
dexter_msgs__srv__AddItem_Response__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *dexter_msgs__srv__AddItem_Response__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
dexter_msgs__srv__AddItem_Event__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[5];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 5, 5};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *dexter_msgs__srv__AddItem_Event__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    sources[2] = *dexter_msgs__srv__AddItem_Request__get_individual_type_description_source(NULL);
    sources[3] = *dexter_msgs__srv__AddItem_Response__get_individual_type_description_source(NULL);
    sources[4] = *service_msgs__msg__ServiceEventInfo__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
