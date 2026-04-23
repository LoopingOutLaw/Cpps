#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__AddTwoInts_Request() -> *const std::ffi::c_void;
}

#[link(name = "dexter_msgs__rosidl_generator_c")]
extern "C" {
    fn dexter_msgs__srv__AddTwoInts_Request__init(msg: *mut AddTwoInts_Request) -> bool;
    fn dexter_msgs__srv__AddTwoInts_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<AddTwoInts_Request>, size: usize) -> bool;
    fn dexter_msgs__srv__AddTwoInts_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<AddTwoInts_Request>);
    fn dexter_msgs__srv__AddTwoInts_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<AddTwoInts_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<AddTwoInts_Request>) -> bool;
}

// Corresponds to dexter_msgs__srv__AddTwoInts_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AddTwoInts_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub a: i64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub b: i64,

}



impl Default for AddTwoInts_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !dexter_msgs__srv__AddTwoInts_Request__init(&mut msg as *mut _) {
        panic!("Call to dexter_msgs__srv__AddTwoInts_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for AddTwoInts_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddTwoInts_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddTwoInts_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddTwoInts_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for AddTwoInts_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for AddTwoInts_Request where Self: Sized {
  const TYPE_NAME: &'static str = "dexter_msgs/srv/AddTwoInts_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__AddTwoInts_Request() }
  }
}


#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__AddTwoInts_Response() -> *const std::ffi::c_void;
}

#[link(name = "dexter_msgs__rosidl_generator_c")]
extern "C" {
    fn dexter_msgs__srv__AddTwoInts_Response__init(msg: *mut AddTwoInts_Response) -> bool;
    fn dexter_msgs__srv__AddTwoInts_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<AddTwoInts_Response>, size: usize) -> bool;
    fn dexter_msgs__srv__AddTwoInts_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<AddTwoInts_Response>);
    fn dexter_msgs__srv__AddTwoInts_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<AddTwoInts_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<AddTwoInts_Response>) -> bool;
}

// Corresponds to dexter_msgs__srv__AddTwoInts_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AddTwoInts_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub sum: i64,

}



impl Default for AddTwoInts_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !dexter_msgs__srv__AddTwoInts_Response__init(&mut msg as *mut _) {
        panic!("Call to dexter_msgs__srv__AddTwoInts_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for AddTwoInts_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddTwoInts_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddTwoInts_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddTwoInts_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for AddTwoInts_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for AddTwoInts_Response where Self: Sized {
  const TYPE_NAME: &'static str = "dexter_msgs/srv/AddTwoInts_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__AddTwoInts_Response() }
  }
}


#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__EulerToQuaternion_Request() -> *const std::ffi::c_void;
}

#[link(name = "dexter_msgs__rosidl_generator_c")]
extern "C" {
    fn dexter_msgs__srv__EulerToQuaternion_Request__init(msg: *mut EulerToQuaternion_Request) -> bool;
    fn dexter_msgs__srv__EulerToQuaternion_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<EulerToQuaternion_Request>, size: usize) -> bool;
    fn dexter_msgs__srv__EulerToQuaternion_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<EulerToQuaternion_Request>);
    fn dexter_msgs__srv__EulerToQuaternion_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<EulerToQuaternion_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<EulerToQuaternion_Request>) -> bool;
}

// Corresponds to dexter_msgs__srv__EulerToQuaternion_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct EulerToQuaternion_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub roll: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pitch: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub yaw: f64,

}



impl Default for EulerToQuaternion_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !dexter_msgs__srv__EulerToQuaternion_Request__init(&mut msg as *mut _) {
        panic!("Call to dexter_msgs__srv__EulerToQuaternion_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for EulerToQuaternion_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__EulerToQuaternion_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__EulerToQuaternion_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__EulerToQuaternion_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for EulerToQuaternion_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for EulerToQuaternion_Request where Self: Sized {
  const TYPE_NAME: &'static str = "dexter_msgs/srv/EulerToQuaternion_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__EulerToQuaternion_Request() }
  }
}


#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__EulerToQuaternion_Response() -> *const std::ffi::c_void;
}

#[link(name = "dexter_msgs__rosidl_generator_c")]
extern "C" {
    fn dexter_msgs__srv__EulerToQuaternion_Response__init(msg: *mut EulerToQuaternion_Response) -> bool;
    fn dexter_msgs__srv__EulerToQuaternion_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<EulerToQuaternion_Response>, size: usize) -> bool;
    fn dexter_msgs__srv__EulerToQuaternion_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<EulerToQuaternion_Response>);
    fn dexter_msgs__srv__EulerToQuaternion_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<EulerToQuaternion_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<EulerToQuaternion_Response>) -> bool;
}

// Corresponds to dexter_msgs__srv__EulerToQuaternion_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct EulerToQuaternion_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub x: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub z: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub w: f64,

}



impl Default for EulerToQuaternion_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !dexter_msgs__srv__EulerToQuaternion_Response__init(&mut msg as *mut _) {
        panic!("Call to dexter_msgs__srv__EulerToQuaternion_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for EulerToQuaternion_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__EulerToQuaternion_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__EulerToQuaternion_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__EulerToQuaternion_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for EulerToQuaternion_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for EulerToQuaternion_Response where Self: Sized {
  const TYPE_NAME: &'static str = "dexter_msgs/srv/EulerToQuaternion_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__EulerToQuaternion_Response() }
  }
}


#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__QuaternionToEuler_Request() -> *const std::ffi::c_void;
}

#[link(name = "dexter_msgs__rosidl_generator_c")]
extern "C" {
    fn dexter_msgs__srv__QuaternionToEuler_Request__init(msg: *mut QuaternionToEuler_Request) -> bool;
    fn dexter_msgs__srv__QuaternionToEuler_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<QuaternionToEuler_Request>, size: usize) -> bool;
    fn dexter_msgs__srv__QuaternionToEuler_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<QuaternionToEuler_Request>);
    fn dexter_msgs__srv__QuaternionToEuler_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<QuaternionToEuler_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<QuaternionToEuler_Request>) -> bool;
}

// Corresponds to dexter_msgs__srv__QuaternionToEuler_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct QuaternionToEuler_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub x: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub z: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub w: f64,

}



impl Default for QuaternionToEuler_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !dexter_msgs__srv__QuaternionToEuler_Request__init(&mut msg as *mut _) {
        panic!("Call to dexter_msgs__srv__QuaternionToEuler_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for QuaternionToEuler_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__QuaternionToEuler_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__QuaternionToEuler_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__QuaternionToEuler_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for QuaternionToEuler_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for QuaternionToEuler_Request where Self: Sized {
  const TYPE_NAME: &'static str = "dexter_msgs/srv/QuaternionToEuler_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__QuaternionToEuler_Request() }
  }
}


#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__QuaternionToEuler_Response() -> *const std::ffi::c_void;
}

#[link(name = "dexter_msgs__rosidl_generator_c")]
extern "C" {
    fn dexter_msgs__srv__QuaternionToEuler_Response__init(msg: *mut QuaternionToEuler_Response) -> bool;
    fn dexter_msgs__srv__QuaternionToEuler_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<QuaternionToEuler_Response>, size: usize) -> bool;
    fn dexter_msgs__srv__QuaternionToEuler_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<QuaternionToEuler_Response>);
    fn dexter_msgs__srv__QuaternionToEuler_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<QuaternionToEuler_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<QuaternionToEuler_Response>) -> bool;
}

// Corresponds to dexter_msgs__srv__QuaternionToEuler_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct QuaternionToEuler_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub roll: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub pitch: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub yaw: f64,

}



impl Default for QuaternionToEuler_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !dexter_msgs__srv__QuaternionToEuler_Response__init(&mut msg as *mut _) {
        panic!("Call to dexter_msgs__srv__QuaternionToEuler_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for QuaternionToEuler_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__QuaternionToEuler_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__QuaternionToEuler_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__QuaternionToEuler_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for QuaternionToEuler_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for QuaternionToEuler_Response where Self: Sized {
  const TYPE_NAME: &'static str = "dexter_msgs/srv/QuaternionToEuler_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__QuaternionToEuler_Response() }
  }
}


#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__DispatchItem_Request() -> *const std::ffi::c_void;
}

#[link(name = "dexter_msgs__rosidl_generator_c")]
extern "C" {
    fn dexter_msgs__srv__DispatchItem_Request__init(msg: *mut DispatchItem_Request) -> bool;
    fn dexter_msgs__srv__DispatchItem_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DispatchItem_Request>, size: usize) -> bool;
    fn dexter_msgs__srv__DispatchItem_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DispatchItem_Request>);
    fn dexter_msgs__srv__DispatchItem_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DispatchItem_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<DispatchItem_Request>) -> bool;
}

// Corresponds to dexter_msgs__srv__DispatchItem_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DispatchItem_Request {
    /// "FIFO" or "FEFO"
    pub mode: rosidl_runtime_rs::String,

}



impl Default for DispatchItem_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !dexter_msgs__srv__DispatchItem_Request__init(&mut msg as *mut _) {
        panic!("Call to dexter_msgs__srv__DispatchItem_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DispatchItem_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__DispatchItem_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__DispatchItem_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__DispatchItem_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DispatchItem_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DispatchItem_Request where Self: Sized {
  const TYPE_NAME: &'static str = "dexter_msgs/srv/DispatchItem_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__DispatchItem_Request() }
  }
}


#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__DispatchItem_Response() -> *const std::ffi::c_void;
}

#[link(name = "dexter_msgs__rosidl_generator_c")]
extern "C" {
    fn dexter_msgs__srv__DispatchItem_Response__init(msg: *mut DispatchItem_Response) -> bool;
    fn dexter_msgs__srv__DispatchItem_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<DispatchItem_Response>, size: usize) -> bool;
    fn dexter_msgs__srv__DispatchItem_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<DispatchItem_Response>);
    fn dexter_msgs__srv__DispatchItem_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<DispatchItem_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<DispatchItem_Response>) -> bool;
}

// Corresponds to dexter_msgs__srv__DispatchItem_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DispatchItem_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub item_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub item_id: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub slot_number: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub expiry_date: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for DispatchItem_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !dexter_msgs__srv__DispatchItem_Response__init(&mut msg as *mut _) {
        panic!("Call to dexter_msgs__srv__DispatchItem_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for DispatchItem_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__DispatchItem_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__DispatchItem_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__DispatchItem_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for DispatchItem_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for DispatchItem_Response where Self: Sized {
  const TYPE_NAME: &'static str = "dexter_msgs/srv/DispatchItem_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__DispatchItem_Response() }
  }
}


#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__AddItem_Request() -> *const std::ffi::c_void;
}

#[link(name = "dexter_msgs__rosidl_generator_c")]
extern "C" {
    fn dexter_msgs__srv__AddItem_Request__init(msg: *mut AddItem_Request) -> bool;
    fn dexter_msgs__srv__AddItem_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<AddItem_Request>, size: usize) -> bool;
    fn dexter_msgs__srv__AddItem_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<AddItem_Request>);
    fn dexter_msgs__srv__AddItem_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<AddItem_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<AddItem_Request>) -> bool;
}

// Corresponds to dexter_msgs__srv__AddItem_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AddItem_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub item_name: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub slot: i32,

    /// Unix timestamp as string; empty = no expiry
    pub expiry_ts: rosidl_runtime_rs::String,

}



impl Default for AddItem_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !dexter_msgs__srv__AddItem_Request__init(&mut msg as *mut _) {
        panic!("Call to dexter_msgs__srv__AddItem_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for AddItem_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddItem_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddItem_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddItem_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for AddItem_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for AddItem_Request where Self: Sized {
  const TYPE_NAME: &'static str = "dexter_msgs/srv/AddItem_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__AddItem_Request() }
  }
}


#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__AddItem_Response() -> *const std::ffi::c_void;
}

#[link(name = "dexter_msgs__rosidl_generator_c")]
extern "C" {
    fn dexter_msgs__srv__AddItem_Response__init(msg: *mut AddItem_Response) -> bool;
    fn dexter_msgs__srv__AddItem_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<AddItem_Response>, size: usize) -> bool;
    fn dexter_msgs__srv__AddItem_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<AddItem_Response>);
    fn dexter_msgs__srv__AddItem_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<AddItem_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<AddItem_Response>) -> bool;
}

// Corresponds to dexter_msgs__srv__AddItem_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AddItem_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub item_id: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for AddItem_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !dexter_msgs__srv__AddItem_Response__init(&mut msg as *mut _) {
        panic!("Call to dexter_msgs__srv__AddItem_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for AddItem_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddItem_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddItem_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { dexter_msgs__srv__AddItem_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for AddItem_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for AddItem_Response where Self: Sized {
  const TYPE_NAME: &'static str = "dexter_msgs/srv/AddItem_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__dexter_msgs__srv__AddItem_Response() }
  }
}






#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__dexter_msgs__srv__AddTwoInts() -> *const std::ffi::c_void;
}

// Corresponds to dexter_msgs__srv__AddTwoInts
#[allow(missing_docs, non_camel_case_types)]
pub struct AddTwoInts;

impl rosidl_runtime_rs::Service for AddTwoInts {
    type Request = AddTwoInts_Request;
    type Response = AddTwoInts_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__dexter_msgs__srv__AddTwoInts() }
    }
}




#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__dexter_msgs__srv__EulerToQuaternion() -> *const std::ffi::c_void;
}

// Corresponds to dexter_msgs__srv__EulerToQuaternion
#[allow(missing_docs, non_camel_case_types)]
pub struct EulerToQuaternion;

impl rosidl_runtime_rs::Service for EulerToQuaternion {
    type Request = EulerToQuaternion_Request;
    type Response = EulerToQuaternion_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__dexter_msgs__srv__EulerToQuaternion() }
    }
}




#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__dexter_msgs__srv__QuaternionToEuler() -> *const std::ffi::c_void;
}

// Corresponds to dexter_msgs__srv__QuaternionToEuler
#[allow(missing_docs, non_camel_case_types)]
pub struct QuaternionToEuler;

impl rosidl_runtime_rs::Service for QuaternionToEuler {
    type Request = QuaternionToEuler_Request;
    type Response = QuaternionToEuler_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__dexter_msgs__srv__QuaternionToEuler() }
    }
}




#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__dexter_msgs__srv__DispatchItem() -> *const std::ffi::c_void;
}

// Corresponds to dexter_msgs__srv__DispatchItem
#[allow(missing_docs, non_camel_case_types)]
pub struct DispatchItem;

impl rosidl_runtime_rs::Service for DispatchItem {
    type Request = DispatchItem_Request;
    type Response = DispatchItem_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__dexter_msgs__srv__DispatchItem() }
    }
}




#[link(name = "dexter_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__dexter_msgs__srv__AddItem() -> *const std::ffi::c_void;
}

// Corresponds to dexter_msgs__srv__AddItem
#[allow(missing_docs, non_camel_case_types)]
pub struct AddItem;

impl rosidl_runtime_rs::Service for AddItem {
    type Request = AddItem_Request;
    type Response = AddItem_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__dexter_msgs__srv__AddItem() }
    }
}


