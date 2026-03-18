// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from dexter_msgs:action/DexterTask.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "dexter_msgs/action/dexter_task.hpp"


#ifndef DEXTER_MSGS__ACTION__DETAIL__DEXTER_TASK__BUILDER_HPP_
#define DEXTER_MSGS__ACTION__DETAIL__DEXTER_TASK__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "dexter_msgs/action/detail/dexter_task__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace dexter_msgs
{

namespace action
{

namespace builder
{

class Init_DexterTask_Goal_task_number
{
public:
  Init_DexterTask_Goal_task_number()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::dexter_msgs::action::DexterTask_Goal task_number(::dexter_msgs::action::DexterTask_Goal::_task_number_type arg)
  {
    msg_.task_number = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_Goal msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::action::DexterTask_Goal>()
{
  return dexter_msgs::action::builder::Init_DexterTask_Goal_task_number();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace action
{

namespace builder
{

class Init_DexterTask_Result_success
{
public:
  Init_DexterTask_Result_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::dexter_msgs::action::DexterTask_Result success(::dexter_msgs::action::DexterTask_Result::_success_type arg)
  {
    msg_.success = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_Result msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::action::DexterTask_Result>()
{
  return dexter_msgs::action::builder::Init_DexterTask_Result_success();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace action
{

namespace builder
{

class Init_DexterTask_Feedback_percentage
{
public:
  Init_DexterTask_Feedback_percentage()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::dexter_msgs::action::DexterTask_Feedback percentage(::dexter_msgs::action::DexterTask_Feedback::_percentage_type arg)
  {
    msg_.percentage = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_Feedback msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::action::DexterTask_Feedback>()
{
  return dexter_msgs::action::builder::Init_DexterTask_Feedback_percentage();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace action
{

namespace builder
{

class Init_DexterTask_SendGoal_Request_goal
{
public:
  explicit Init_DexterTask_SendGoal_Request_goal(::dexter_msgs::action::DexterTask_SendGoal_Request & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::action::DexterTask_SendGoal_Request goal(::dexter_msgs::action::DexterTask_SendGoal_Request::_goal_type arg)
  {
    msg_.goal = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_SendGoal_Request msg_;
};

class Init_DexterTask_SendGoal_Request_goal_id
{
public:
  Init_DexterTask_SendGoal_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DexterTask_SendGoal_Request_goal goal_id(::dexter_msgs::action::DexterTask_SendGoal_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_DexterTask_SendGoal_Request_goal(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_SendGoal_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::action::DexterTask_SendGoal_Request>()
{
  return dexter_msgs::action::builder::Init_DexterTask_SendGoal_Request_goal_id();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace action
{

namespace builder
{

class Init_DexterTask_SendGoal_Response_stamp
{
public:
  explicit Init_DexterTask_SendGoal_Response_stamp(::dexter_msgs::action::DexterTask_SendGoal_Response & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::action::DexterTask_SendGoal_Response stamp(::dexter_msgs::action::DexterTask_SendGoal_Response::_stamp_type arg)
  {
    msg_.stamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_SendGoal_Response msg_;
};

class Init_DexterTask_SendGoal_Response_accepted
{
public:
  Init_DexterTask_SendGoal_Response_accepted()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DexterTask_SendGoal_Response_stamp accepted(::dexter_msgs::action::DexterTask_SendGoal_Response::_accepted_type arg)
  {
    msg_.accepted = std::move(arg);
    return Init_DexterTask_SendGoal_Response_stamp(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_SendGoal_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::action::DexterTask_SendGoal_Response>()
{
  return dexter_msgs::action::builder::Init_DexterTask_SendGoal_Response_accepted();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace action
{

namespace builder
{

class Init_DexterTask_SendGoal_Event_response
{
public:
  explicit Init_DexterTask_SendGoal_Event_response(::dexter_msgs::action::DexterTask_SendGoal_Event & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::action::DexterTask_SendGoal_Event response(::dexter_msgs::action::DexterTask_SendGoal_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_SendGoal_Event msg_;
};

class Init_DexterTask_SendGoal_Event_request
{
public:
  explicit Init_DexterTask_SendGoal_Event_request(::dexter_msgs::action::DexterTask_SendGoal_Event & msg)
  : msg_(msg)
  {}
  Init_DexterTask_SendGoal_Event_response request(::dexter_msgs::action::DexterTask_SendGoal_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_DexterTask_SendGoal_Event_response(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_SendGoal_Event msg_;
};

class Init_DexterTask_SendGoal_Event_info
{
public:
  Init_DexterTask_SendGoal_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DexterTask_SendGoal_Event_request info(::dexter_msgs::action::DexterTask_SendGoal_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_DexterTask_SendGoal_Event_request(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_SendGoal_Event msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::action::DexterTask_SendGoal_Event>()
{
  return dexter_msgs::action::builder::Init_DexterTask_SendGoal_Event_info();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace action
{

namespace builder
{

class Init_DexterTask_GetResult_Request_goal_id
{
public:
  Init_DexterTask_GetResult_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::dexter_msgs::action::DexterTask_GetResult_Request goal_id(::dexter_msgs::action::DexterTask_GetResult_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_GetResult_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::action::DexterTask_GetResult_Request>()
{
  return dexter_msgs::action::builder::Init_DexterTask_GetResult_Request_goal_id();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace action
{

namespace builder
{

class Init_DexterTask_GetResult_Response_result
{
public:
  explicit Init_DexterTask_GetResult_Response_result(::dexter_msgs::action::DexterTask_GetResult_Response & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::action::DexterTask_GetResult_Response result(::dexter_msgs::action::DexterTask_GetResult_Response::_result_type arg)
  {
    msg_.result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_GetResult_Response msg_;
};

class Init_DexterTask_GetResult_Response_status
{
public:
  Init_DexterTask_GetResult_Response_status()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DexterTask_GetResult_Response_result status(::dexter_msgs::action::DexterTask_GetResult_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_DexterTask_GetResult_Response_result(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_GetResult_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::action::DexterTask_GetResult_Response>()
{
  return dexter_msgs::action::builder::Init_DexterTask_GetResult_Response_status();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace action
{

namespace builder
{

class Init_DexterTask_GetResult_Event_response
{
public:
  explicit Init_DexterTask_GetResult_Event_response(::dexter_msgs::action::DexterTask_GetResult_Event & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::action::DexterTask_GetResult_Event response(::dexter_msgs::action::DexterTask_GetResult_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_GetResult_Event msg_;
};

class Init_DexterTask_GetResult_Event_request
{
public:
  explicit Init_DexterTask_GetResult_Event_request(::dexter_msgs::action::DexterTask_GetResult_Event & msg)
  : msg_(msg)
  {}
  Init_DexterTask_GetResult_Event_response request(::dexter_msgs::action::DexterTask_GetResult_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_DexterTask_GetResult_Event_response(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_GetResult_Event msg_;
};

class Init_DexterTask_GetResult_Event_info
{
public:
  Init_DexterTask_GetResult_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DexterTask_GetResult_Event_request info(::dexter_msgs::action::DexterTask_GetResult_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_DexterTask_GetResult_Event_request(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_GetResult_Event msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::action::DexterTask_GetResult_Event>()
{
  return dexter_msgs::action::builder::Init_DexterTask_GetResult_Event_info();
}

}  // namespace dexter_msgs


namespace dexter_msgs
{

namespace action
{

namespace builder
{

class Init_DexterTask_FeedbackMessage_feedback
{
public:
  explicit Init_DexterTask_FeedbackMessage_feedback(::dexter_msgs::action::DexterTask_FeedbackMessage & msg)
  : msg_(msg)
  {}
  ::dexter_msgs::action::DexterTask_FeedbackMessage feedback(::dexter_msgs::action::DexterTask_FeedbackMessage::_feedback_type arg)
  {
    msg_.feedback = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_FeedbackMessage msg_;
};

class Init_DexterTask_FeedbackMessage_goal_id
{
public:
  Init_DexterTask_FeedbackMessage_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_DexterTask_FeedbackMessage_feedback goal_id(::dexter_msgs::action::DexterTask_FeedbackMessage::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_DexterTask_FeedbackMessage_feedback(msg_);
  }

private:
  ::dexter_msgs::action::DexterTask_FeedbackMessage msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::dexter_msgs::action::DexterTask_FeedbackMessage>()
{
  return dexter_msgs::action::builder::Init_DexterTask_FeedbackMessage_goal_id();
}

}  // namespace dexter_msgs

#endif  // DEXTER_MSGS__ACTION__DETAIL__DEXTER_TASK__BUILDER_HPP_
