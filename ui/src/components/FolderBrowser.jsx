/**
 * FolderBrowser Component
 * Browse tickets by Marketplace > Category > Folder hierarchy
 */
import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import './FolderBrowser.css';

export default function FolderBrowser({ onFolderSelect }) {
  const [marketplaces, setMarketplaces] = useState([]);
  const [selectedMarketplace, setSelectedMarketplace] = useState(null);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [folders, setFolders] = useState([]);
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load marketplaces on mount
  useEffect(() => {
    loadMarketplaces();
  }, []);

  // Load categories when marketplace changes
  useEffect(() => {
    if (selectedMarketplace) {
      loadCategories(selectedMarketplace.id);
    } else {
      setCategories([]);
      setSelectedCategory(null);
    }
  }, [selectedMarketplace]);

  // Load folders when category changes
  useEffect(() => {
    if (selectedCategory) {
      loadFolders(selectedCategory.id);
    } else {
      setFolders([]);
      setSelectedFolder(null);
    }
  }, [selectedCategory]);

  // Notify parent when folder selection changes
  useEffect(() => {
    if (onFolderSelect) {
      onFolderSelect(selectedFolder);
    }
  }, [selectedFolder, onFolderSelect]);

  const loadMarketplaces = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMarketplaces();
      setMarketplaces(data);
    } catch (err) {
      setError('Failed to load marketplaces');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async (marketplaceId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getCategories(marketplaceId);
      setCategories(data);
    } catch (err) {
      setError('Failed to load categories');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadFolders = async (categoryId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getFolders(categoryId);
      setFolders(data);
    } catch (err) {
      setError('Failed to load folders');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="folder-browser">
      <h2>Browse Tickets</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="browser-section">
        <h3>Marketplace</h3>
        <div className="item-list">
          {marketplaces.map((marketplace) => (
            <div
              key={marketplace.id}
              className={`item ${selectedMarketplace?.id === marketplace.id ? 'selected' : ''}`}
              onClick={() => setSelectedMarketplace(marketplace)}
            >
              <strong>{marketplace.name}</strong>
              <span className="item-code">{marketplace.code}</span>
            </div>
          ))}
        </div>
      </div>

      {selectedMarketplace && (
        <div className="browser-section">
          <h3>Category</h3>
          <div className="item-list">
            {categories.map((category) => (
              <div
                key={category.id}
                className={`item ${selectedCategory?.id === category.id ? 'selected' : ''}`}
                onClick={() => setSelectedCategory(category)}
              >
                <strong>{category.name}</strong>
                {category.description && <span className="item-desc">{category.description}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedCategory && (
        <div className="browser-section">
          <h3>Folder</h3>
          <div className="item-list">
            {folders.map((folder) => (
              <div
                key={folder.id}
                className={`item ${selectedFolder?.id === folder.id ? 'selected' : ''}`}
                onClick={() => setSelectedFolder(folder)}
              >
                <strong>{folder.name}</strong>
                {folder.path && <span className="item-path">{folder.path}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {loading && <div className="loading">Loading...</div>}
    </div>
  );
}
