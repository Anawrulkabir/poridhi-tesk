import React, { useState } from 'react' // Corrected import for useState
import axios from 'axios'
import './TaskForm.css' // We'll create this for styling

const API_ENDPOINT = 'https://poridhi-tesk.vercel.app/add_task'

function TaskForm() {
  const [name, setName] = useState('')
  const [taskName, setTaskName] = useState('')
  const [repoLink, setRepoLink] = useState('')
  const [taskUpdates, setTaskUpdates] = useState([{ text: '', link: '' }])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const handleUpdateChange = (index, field, value) => {
    const newUpdates = [...taskUpdates]
    newUpdates[index][field] = value
    setTaskUpdates(newUpdates)
  }

  const addUpdateField = () => {
    setTaskUpdates([...taskUpdates, { text: '', link: '' }])
  }

  const removeUpdateField = (index) => {
    const newUpdates = taskUpdates.filter((_, i) => i !== index)
    setTaskUpdates(newUpdates)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage('')
    setError('')

    if (
      !name ||
      !taskName ||
      !repoLink ||
      taskUpdates.some((upd) => !upd.text)
    ) {
      setError(
        'Please fill in all required fields (Name, Task Name, Repo Link, and at least one update text).'
      )
      return
    }

    const payload = {
      name,
      task_name: taskName,
      task_updates: taskUpdates.map((upd) => ({
        text: upd.text,
        link: upd.link || '',
      })),
      repo_link: repoLink,
    }

    try {
      const response = await axios.post(API_ENDPOINT, payload)
      setMessage(
        'Task submitted successfully! Task ID: ' + response.data.task_id
      )
      // Clear form
      setName('')
      setTaskName('')
      setRepoLink('')
      setTaskUpdates([{ text: '', link: '' }])
    } catch (err) {
      setError(
        'Failed to submit task. ' + (err.response?.data?.error || err.message)
      )
      console.error(err)
    }
  }

  return (
    <div className="task-form-container">
      <h2>Submit Task Update</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="name">Your Name:</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="taskName">Task Name:</label>
          <input
            type="text"
            id="taskName"
            value={taskName}
            onChange={(e) => setTaskName(e.target.value)}
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="repoLink">Repository Link:</label>
          <input
            type="url"
            id="repoLink"
            value={repoLink}
            onChange={(e) => setRepoLink(e.target.value)}
            required
          />
        </div>

        <h3>Task Updates:</h3>
        {taskUpdates.map((update, index) => (
          <div key={index} className="task-update-item">
            <div className="form-group">
              <label htmlFor={`updateText-${index}`}>
                Update Text #{index + 1}:
              </label>
              <textarea
                id={`updateText-${index}`}
                value={update.text}
                onChange={(e) =>
                  handleUpdateChange(index, 'text', e.target.value)
                }
                required
                rows="3"
              />
            </div>
            <div className="form-group">
              <label htmlFor={`updateLink-${index}`}>
                Optional Link for Update #{index + 1}:
              </label>
              <input
                type="url"
                id={`updateLink-${index}`}
                value={update.link}
                onChange={(e) =>
                  handleUpdateChange(index, 'link', e.target.value)
                }
              />
            </div>
            {taskUpdates.length > 1 && (
              <button
                type="button"
                className="remove-update-btn"
                onClick={() => removeUpdateField(index)}
              >
                Remove Update
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          className="add-update-btn"
          onClick={addUpdateField}
        >
          Add Another Update
        </button>

        <button type="submit" className="submit-btn">
          Submit Task
        </button>
      </form>
      {message && <p className="success-message">{message}</p>}
      {error && <p className="error-message">{error}</p>}
    </div>
  )
}

export default TaskForm
