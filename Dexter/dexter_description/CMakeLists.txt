cmake_minimum_required(VERSION 3.5)
project(dexter_description)

find_package(ament_cmake REQUIRED)
find_package(Python3 COMPONENTS Interpreter)

# ── Auto-generate ArUco texture PNGs if they are missing ─────────────────────
# The textures are used by inventory.sdf for the overhead-camera ArUco markers.
# We generate them at configure time so they are present before install.
# The script falls back gracefully if opencv-python is not installed.

set(TEXTURE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/textures")
set(TEXTURE_SCRIPT "${CMAKE_CURRENT_SOURCE_DIR}/scripts/generate_aruco_textures.py")
set(SENTINEL "${TEXTURE_DIR}/aruco_13.png")  # last marker to be generated

if(Python3_Interpreter_FOUND AND EXISTS "${TEXTURE_SCRIPT}")
  if(NOT EXISTS "${SENTINEL}")
    message(STATUS "ArUco textures missing — generating with ${TEXTURE_SCRIPT}")
    execute_process(
      COMMAND "${Python3_EXECUTABLE}" "${TEXTURE_SCRIPT}" "${TEXTURE_DIR}"
      RESULT_VARIABLE _tex_result
      OUTPUT_VARIABLE _tex_output
      ERROR_VARIABLE  _tex_error
    )
    if(_tex_result)
      message(WARNING
        "ArUco texture generation failed (exit ${_tex_result}):\n${_tex_error}\n"
        "Simulation will load but ArUco detection may not work in Gazebo.")
    else()
      message(STATUS "ArUco textures generated:\n${_tex_output}")
    endif()
  else()
    message(STATUS "ArUco textures already exist — skipping generation")
  endif()
else()
  message(WARNING
    "Python3 or texture script not found — ArUco textures will not be generated.\n"
    "Run manually:  python3 ${TEXTURE_SCRIPT}")
endif()
# ─────────────────────────────────────────────────────────────────────────────

install(
  DIRECTORY launch meshes urdf rviz worlds textures scripts
  DESTINATION share/${PROJECT_NAME}
  # Don't fail if textures/ doesn't exist yet
  OPTIONAL
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
