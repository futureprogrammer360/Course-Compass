function CourseInfo({ courseData }) {
  if (courseData === null) {
    return null;
  }
  let hasCodes, hasCrossListedAs, hasTypicallyOffered, needs2Columns;
  if (!courseData.hasError) {
    if (courseData.description === null) {
      courseData.description = "";
    }
    hasCodes = courseData.codes.length > 0;
    hasCrossListedAs = courseData.cross_listed_as.length > 0;
    hasTypicallyOffered = Boolean(courseData.typically_offered);
    needs2Columns = hasCodes || hasCrossListedAs || hasTypicallyOffered;
  }
  return (
    <div id="course-info">
      {courseData.hasError ? (
        <p>{courseData.errorMessage}</p>
      ) : (
        <>
          <h1>{courseData.title}</h1>

          <div className={needs2Columns && "column-container"}>

            <div className={needs2Columns && "left-column"}>
              <h1>{courseData.number}</h1>
              <p>
                {
                  courseData.description.split('\n').map((line, index) => (<>
                    {index !== 0 && <><br /><br /></>}
                    {line}
                  </>))
                }
              </p>
              <p>
                <a href={courseData.url} target="_blank">Course Info Page</a>
                &nbsp;|&nbsp;
                <a href={`https://www.google.com/search?q=${courseData.number}`} target="_blank">Google Search</a>
              </p>
            </div>

            {
              needs2Columns &&
              <div className="right-column">
                {
                  hasCodes &&
                  <>
                    <h3>Curriculum Codes</h3>
                    <ul>
                      {
                        courseData.codes.map((code, index) => (
                          <li key={index}>{code}</li>
                        ))
                      }
                    </ul>
                  </>
                }

                {
                  hasCrossListedAs &&
                  <>
                    <h3>Cross-Listed As</h3>
                    <ul>
                      {
                        courseData.cross_listed_as.map((number, index) => (
                          <li key={index}>{number}</li>
                        ))
                      }
                    </ul>
                  </>
                }

                {
                  hasTypicallyOffered &&
                  <>
                    <h3>Typically Offered</h3>
                    <p>{courseData.typically_offered}</p>
                  </>
                }
              </div>
            }

          </div>
        </>
      )}
    </div>
  );
}

export default CourseInfo;
