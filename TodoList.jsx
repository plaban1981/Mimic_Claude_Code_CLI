import React, { useState } from 'react';
import './TodoList.css';

/**
 * TodoList Component
 * A fully functional todo list with add, complete, delete, and filter features
 */
const TodoList = () => {
  const [todos, setTodos] = useState([
    { id: 1, text: 'Learn React', completed: false },
    { id: 2, text: 'Build a todo app', completed: false },
    { id: 3, text: 'Master JavaScript', completed: true },
  ]);
  
  const [inputValue, setInputValue] = useState('');
  const [filter, setFilter] = useState('all'); // 'all', 'active', 'completed'
  const [nextId, setNextId] = useState(4);

  // Add a new todo
  const handleAddTodo = (e) => {
    e.preventDefault();
    
    if (inputValue.trim() === '') {
      return;
    }

    const newTodo = {
      id: nextId,
      text: inputValue.trim(),
      completed: false,
    };

    setTodos([...todos, newTodo]);
    setInputValue('');
    setNextId(nextId + 1);
  };

  // Toggle todo completion status
  const handleToggleTodo = (id) => {
    setTodos(
      todos.map((todo) =>
        todo.id === id ? { ...todo, completed: !todo.completed } : todo
      )
    );
  };

  // Delete a todo
  const handleDeleteTodo = (id) => {
    setTodos(todos.filter((todo) => todo.id !== id));
  };

  // Clear all completed todos
  const handleClearCompleted = () => {
    setTodos(todos.filter((todo) => !todo.completed));
  };

  // Get filtered todos based on current filter
  const getFilteredTodos = () => {
    switch (filter) {
      case 'active':
        return todos.filter((todo) => !todo.completed);
      case 'completed':
        return todos.filter((todo) => todo.completed);
      default:
        return todos;
    }
  };

  // Calculate statistics
  const activeTodosCount = todos.filter((todo) => !todo.completed).length;
  const completedTodosCount = todos.filter((todo) => todo.completed).length;
  const filteredTodos = getFilteredTodos();

  return (
    <div className="todo-container">
      <div className="todo-app">
        <h1 className="todo-title">📝 My Todo List</h1>
        
        {/* Add Todo Form */}
        <form onSubmit={handleAddTodo} className="todo-form">
          <input
            type="text"
            className="todo-input"
            placeholder="What needs to be done?"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
          <button type="submit" className="todo-add-btn">
            Add
          </button>
        </form>

        {/* Statistics */}
        <div className="todo-stats">
          <span className="stat-item">
            Total: <strong>{todos.length}</strong>
          </span>
          <span className="stat-item">
            Active: <strong>{activeTodosCount}</strong>
          </span>
          <span className="stat-item">
            Completed: <strong>{completedTodosCount}</strong>
          </span>
        </div>

        {/* Filter Buttons */}
        <div className="todo-filters">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button
            className={`filter-btn ${filter === 'active' ? 'active' : ''}`}
            onClick={() => setFilter('active')}
          >
            Active
          </button>
          <button
            className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
            onClick={() => setFilter('completed')}
          >
            Completed
          </button>
        </div>

        {/* Todo List */}
        <ul className="todo-list">
          {filteredTodos.length === 0 ? (
            <li className="todo-empty">
              {filter === 'all' && 'No todos yet. Add one above!'}
              {filter === 'active' && 'No active todos. Great job! 🎉'}
              {filter === 'completed' && 'No completed todos yet.'}
            </li>
          ) : (
            filteredTodos.map((todo) => (
              <li
                key={todo.id}
                className={`todo-item ${todo.completed ? 'completed' : ''}`}
              >
                <div className="todo-content">
                  <input
                    type="checkbox"
                    className="todo-checkbox"
                    checked={todo.completed}
                    onChange={() => handleToggleTodo(todo.id)}
                  />
                  <span
                    className="todo-text"
                    onClick={() => handleToggleTodo(todo.id)}
                  >
                    {todo.text}
                  </span>
                </div>
                <button
                  className="todo-delete-btn"
                  onClick={() => handleDeleteTodo(todo.id)}
                  aria-label="Delete todo"
                >
                  ✕
                </button>
              </li>
            ))
          )}
        </ul>

        {/* Clear Completed Button */}
        {completedTodosCount > 0 && (
          <div className="todo-actions">
            <button
              className="clear-completed-btn"
              onClick={handleClearCompleted}
            >
              Clear Completed ({completedTodosCount})
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default TodoList;
