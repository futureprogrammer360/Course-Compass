import { useState, useEffect } from 'react';
import './Popup.css';
import CourseSearchForm from './components/CourseSearchForm.jsx';
import CourseInfo from './components/CourseInfo.jsx';

const API_URL = process.env.API_URL;

function Popup() {
  const [courseData, setCourseData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');

  const searchListener = (message, sender, sendResponse) => {
    search(message.query);
    setInputValue(message.query);
  }

  useEffect(() => {
    chrome.runtime.onMessage.addListener(searchListener);
    return () => chrome.runtime.onMessage.removeListener(searchListener);
  }, []);

  async function fetchCourseData(universityId, courseNumber, limit = 1) {
    let url = new URL(`${API_URL}/courses/${universityId}`);
    let params = {
      limit: limit,
      query: courseNumber
    };
    url.search = new URLSearchParams(params).toString();

    try {
      let response = await fetch(url.toString());
      return response;
    } catch (e) {
      return null;
    }
  }

  let search = async courseNumber => {
    setIsLoading(true);
    let response = await fetchCourseData('duke_university', courseNumber);
    setIsLoading(false);

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
        document.body.style.width = '800px';
        document.body.style.paddingBottom = 0;
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
      <CourseSearchForm
        searchCallback={search}
        inputValue={inputValue}
        setInputValue={setInputValue}
      />
      {isLoading ? (
        <p>Loading...</p>
      ) : (
        <CourseInfo courseData={courseData} />
      )}
    </>
  );
}

export default Popup;
