import React, { useState } from 'react';
import './App.css';

const API_URL = 'http://127.0.0.1:8000/api';

function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
    } else {
      alert('Please select a PDF file');
    }
  };

  const uploadManual = async () => {
    if (!file) {
      alert('Please select a file first');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(API_URL + '/upload/', { // Added /upload/
  method: 'POST',
  body: formData,
});

      if (!response.ok) throw new Error('Upload failed');

      const data = await response.json();
      alert(data.message);
      setUploaded(true);
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  const askQuestion = async () => {
    if (!question.trim()) return;

    const userMessage = { type: 'user', text: question };
    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setLoading(true);

    try {
      const response = await fetch(API_URL + '/ask/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question }),
      });

      if (!response.ok) throw new Error('Failed to get answer');

      const data = await response.json();
      const botMessage = {
        type: 'bot',
        text: data.answer,
        sources: data.sources
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'bot',
        text: 'Error: ' + error.message
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🛵 Aprilia SR125 Assistant</h1>
        <p>Your Personal Scooter Manual Chatbot</p>
      </header>

      {!uploaded && (
        <div className="upload-section">
          <h2>Upload Your Manual</h2>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            disabled={uploading}
          />
          <button
            onClick={uploadManual}
            disabled={!file || uploading}
            className="upload-btn"
          >
            {uploading ? 'Uploading...' : 'Upload & Process'}
          </button>
        </div>
      )}

      {uploaded && (
        <div className="chat-section">
          <div className="chat-box">
            {messages.length === 0 && (
              <div className="welcome-message">
                <p>Manual uploaded! Ask anything about your Aprilia SR125.</p>
                <p className="examples">Try: "How do I change the oil?"</p>
              </div>
            )}

            {messages.map((msg, index) => (
              <div key={index} className={'message ' + msg.type + '-message'}>
                <div className="message-content">
                  {msg.text}
                  {msg.sources && <div className="sources">{msg.sources}</div>}
                </div>
              </div>
            ))}

            {loading && (
              <div className="message bot-message">
                <div className="message-content">Thinking...</div>
              </div>
            )}
          </div>

          <div className="input-section">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about your scooter..."
              disabled={loading}
            />
            <button onClick={askQuestion} disabled={!question.trim() || loading}>
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;