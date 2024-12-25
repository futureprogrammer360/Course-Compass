import { useState } from 'react';
import './Popup.css';
import CourseSearchForm from './components/CourseSearchForm.jsx';
import CourseInfo from './components/CourseInfo.jsx';

function Popup() {
  const [courseData, setCourseData] = useState(null);

  async function fetchCourseData(universityId, courseNumber, limit = 1) {
    let url = `http://0.0.0.0:8000/courses/${universityId}?limit=${limit}&query=${courseNumber}`;
    try {
      let response = await fetch(url);
      return response;
    } catch (e) {
      return null;
    }
  }

  let search = async courseNumber => {
    let response = await fetchCourseData('duke_university', courseNumber.toUpperCase());

    if (response === null) {
      setCourseData({
        hasError: true,
        errorMessage: 'API connection failed: check network connection'
      });
      return;
    }

    if (response.ok) {
      let data = await response.json();
      if (data.length > 0) {
        let courseData = data[0];
        setCourseData({
          hasError: false,
          ...courseData
        });
      } else {
        setCourseData({
          hasError: true,
          errorMessage: 'No course found'
        });
      }
    }
  };

  return (
    <>
      <CourseSearchForm searchCallback={search} />
      <CourseInfo courseData={courseData} />
    </>
  );
}

export default Popup;
