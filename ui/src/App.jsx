import { useState } from 'react'
import FolderBrowser from './components/FolderBrowser'
import TicketGrid from './components/TicketGrid'
import './App.css'

function App() {
  const [selectedFolder, setSelectedFolder] = useState(null)

  return (
    <div className="app">
      <header className="app-header">
        <h1>📧 Fulfillment Ticket System</h1>
        <p>Manage your tickets, claims, and fulfillment operations</p>
      </header>

      <div className="app-content">
        <aside className="sidebar">
          <FolderBrowser onFolderSelect={setSelectedFolder} />
        </aside>

        <main className="main-content">
          {selectedFolder ? (
            <>
              <div className="content-header">
                <h2>{selectedFolder.name}</h2>
                {selectedFolder.description && (
                  <p className="folder-description">{selectedFolder.description}</p>
                )}
              </div>
              <TicketGrid folderId={selectedFolder.id} />
            </>
          ) : (
            <div className="welcome-message">
              <h2>Welcome to the Fulfillment Ticket System</h2>
              <p>Select a marketplace, category, and folder from the sidebar to view tickets.</p>
              <div className="features">
                <div className="feature">
                  <h3>📁 Browse by Hierarchy</h3>
                  <p>Navigate through Marketplace → Category → Folder</p>
                </div>
                <div className="feature">
                  <h3>🎫 Ticket Management</h3>
                  <p>View and manage fulfillment tickets with detailed information</p>
                </div>
                <div className="feature">
                  <h3>📊 Track Claims</h3>
                  <p>Monitor claims, payments, and order status</p>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App

