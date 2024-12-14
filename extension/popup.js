async function fetchCourseData(universityId, courseId) {
  let url = `http://0.0.0.0:8000/course/${universityId}/${courseId}`;
  try {
    let response = await fetch(url);
    return response.json();
  } catch (e) {
    return null;
  }
}

document.getElementById("course-number-form").addEventListener("submit", event => {
  event.preventDefault();

  let courseNumber = document.getElementById("course-number-input").value.trim();
  if (!courseNumber) {
    return;
  }
  let courseId = courseNumber.toLowerCase().replace(" ", "_").replace("-", "_");

  let courseInfoDiv = document.getElementById("course-info");
  courseInfoDiv.innerHTML = "<p>Loading course info...</p>";

  fetchCourseData("duke_university", courseId)
    .then(data => {
      if (data !== null) {
        if (data.code === 200) {
          let courseData = data.course;
          courseInfoDiv.innerHTML = `
            <h3>${courseData.title}</h3>
            <p>${courseData.description}</p>
          `;
        } else {
          courseInfoDiv.innerHTML = "<p>No course found</p>";
        }
      } else {
        courseInfoDiv.innerHTML = "<p>Cannot connect to API</p>";
      }
    });
});
