function CourseInfo({ courseData }) {
  if (courseData === null) {
    return null;
  }
  return (
    <div id="course-info">
      {courseData.hasError ? (
        <p>{courseData.errorMessage}</p>
      ) : (
        <>
          <h1>{courseData.title}</h1>
          <h2>{courseData.number}</h2>
          <p>
            {courseData.description.split('\n').map((line, index) => (
              <>
                {index !== 0 && <><br /><br /></>}
                {line}
              </>
            ))}
          </p>
          <p><a href={courseData.url} target="_blank">Course Info Page</a></p>
        </>
      )}
    </div>
  );
}

export default CourseInfo;
