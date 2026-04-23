#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to dexter_msgs__srv__AddTwoInts_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::AddTwoInts_Request::default())
  }
}

impl rosidl_runtime_rs::Message for AddTwoInts_Request {
  type RmwMsg = super::srv::rmw::AddTwoInts_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        a: msg.a,
        b: msg.b,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      a: msg.a,
      b: msg.b,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      a: msg.a,
      b: msg.b,
    }
  }
}


// Corresponds to dexter_msgs__srv__AddTwoInts_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AddTwoInts_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub sum: i64,

}



impl Default for AddTwoInts_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::AddTwoInts_Response::default())
  }
}

impl rosidl_runtime_rs::Message for AddTwoInts_Response {
  type RmwMsg = super::srv::rmw::AddTwoInts_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        sum: msg.sum,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      sum: msg.sum,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      sum: msg.sum,
    }
  }
}


// Corresponds to dexter_msgs__srv__EulerToQuaternion_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::EulerToQuaternion_Request::default())
  }
}

impl rosidl_runtime_rs::Message for EulerToQuaternion_Request {
  type RmwMsg = super::srv::rmw::EulerToQuaternion_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        roll: msg.roll,
        pitch: msg.pitch,
        yaw: msg.yaw,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      roll: msg.roll,
      pitch: msg.pitch,
      yaw: msg.yaw,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      roll: msg.roll,
      pitch: msg.pitch,
      yaw: msg.yaw,
    }
  }
}


// Corresponds to dexter_msgs__srv__EulerToQuaternion_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::EulerToQuaternion_Response::default())
  }
}

impl rosidl_runtime_rs::Message for EulerToQuaternion_Response {
  type RmwMsg = super::srv::rmw::EulerToQuaternion_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        x: msg.x,
        y: msg.y,
        z: msg.z,
        w: msg.w,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      x: msg.x,
      y: msg.y,
      z: msg.z,
      w: msg.w,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      x: msg.x,
      y: msg.y,
      z: msg.z,
      w: msg.w,
    }
  }
}


// Corresponds to dexter_msgs__srv__QuaternionToEuler_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::QuaternionToEuler_Request::default())
  }
}

impl rosidl_runtime_rs::Message for QuaternionToEuler_Request {
  type RmwMsg = super::srv::rmw::QuaternionToEuler_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        x: msg.x,
        y: msg.y,
        z: msg.z,
        w: msg.w,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      x: msg.x,
      y: msg.y,
      z: msg.z,
      w: msg.w,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      x: msg.x,
      y: msg.y,
      z: msg.z,
      w: msg.w,
    }
  }
}


// Corresponds to dexter_msgs__srv__QuaternionToEuler_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::QuaternionToEuler_Response::default())
  }
}

impl rosidl_runtime_rs::Message for QuaternionToEuler_Response {
  type RmwMsg = super::srv::rmw::QuaternionToEuler_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        roll: msg.roll,
        pitch: msg.pitch,
        yaw: msg.yaw,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      roll: msg.roll,
      pitch: msg.pitch,
      yaw: msg.yaw,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      roll: msg.roll,
      pitch: msg.pitch,
      yaw: msg.yaw,
    }
  }
}


// Corresponds to dexter_msgs__srv__DispatchItem_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DispatchItem_Request {
    /// "FIFO" or "FEFO"
    pub mode: std::string::String,

}



impl Default for DispatchItem_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::DispatchItem_Request::default())
  }
}

impl rosidl_runtime_rs::Message for DispatchItem_Request {
  type RmwMsg = super::srv::rmw::DispatchItem_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        mode: msg.mode.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        mode: msg.mode.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      mode: msg.mode.to_string(),
    }
  }
}


// Corresponds to dexter_msgs__srv__DispatchItem_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct DispatchItem_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub item_name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub item_id: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub slot_number: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub expiry_date: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for DispatchItem_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::DispatchItem_Response::default())
  }
}

impl rosidl_runtime_rs::Message for DispatchItem_Response {
  type RmwMsg = super::srv::rmw::DispatchItem_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        item_name: msg.item_name.as_str().into(),
        item_id: msg.item_id.as_str().into(),
        slot_number: msg.slot_number,
        expiry_date: msg.expiry_date.as_str().into(),
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        item_name: msg.item_name.as_str().into(),
        item_id: msg.item_id.as_str().into(),
      slot_number: msg.slot_number,
        expiry_date: msg.expiry_date.as_str().into(),
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      item_name: msg.item_name.to_string(),
      item_id: msg.item_id.to_string(),
      slot_number: msg.slot_number,
      expiry_date: msg.expiry_date.to_string(),
      message: msg.message.to_string(),
    }
  }
}


// Corresponds to dexter_msgs__srv__AddItem_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AddItem_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub item_name: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub slot: i32,

    /// Unix timestamp as string; empty = no expiry
    pub expiry_ts: std::string::String,

}



impl Default for AddItem_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::AddItem_Request::default())
  }
}

impl rosidl_runtime_rs::Message for AddItem_Request {
  type RmwMsg = super::srv::rmw::AddItem_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        item_name: msg.item_name.as_str().into(),
        slot: msg.slot,
        expiry_ts: msg.expiry_ts.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        item_name: msg.item_name.as_str().into(),
      slot: msg.slot,
        expiry_ts: msg.expiry_ts.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      item_name: msg.item_name.to_string(),
      slot: msg.slot,
      expiry_ts: msg.expiry_ts.to_string(),
    }
  }
}


// Corresponds to dexter_msgs__srv__AddItem_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct AddItem_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub item_id: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: std::string::String,

}



impl Default for AddItem_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::AddItem_Response::default())
  }
}

impl rosidl_runtime_rs::Message for AddItem_Response {
  type RmwMsg = super::srv::rmw::AddItem_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        success: msg.success,
        item_id: msg.item_id.as_str().into(),
        message: msg.message.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      success: msg.success,
        item_id: msg.item_id.as_str().into(),
        message: msg.message.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      success: msg.success,
      item_id: msg.item_id.to_string(),
      message: msg.message.to_string(),
    }
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


