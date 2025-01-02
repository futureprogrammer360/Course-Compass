import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSearch } from '@fortawesome/free-solid-svg-icons';

function CourseSearchForm({ searchCallback, inputValue, setInputValue }) {
  let onSubmit = e => {
    e.preventDefault();
    let formData = new FormData(e.target);
    let courseNumber = formData.get('course-number-input').trim();
    if (courseNumber) {
      searchCallback(courseNumber);
    }
  };

  let onChange = e => {
    setInputValue(e.target.value);
  };

  return (
    <form id="course-number-form" onSubmit={onSubmit}>
      <input
        type="text"
        name="course-number-input"
        placeholder="Course Number e.g. COMPSCI 101L"
        value={inputValue}
        onChange={onChange}
        autoComplete="off"
        autoFocus
      />
      <button type="submit">
        <FontAwesomeIcon icon={faSearch} />
      </button>
    </form>
  );
}

export default CourseSearchForm;
