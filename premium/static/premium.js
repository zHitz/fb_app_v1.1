// Premium Facebook Scraper JavaScript
class PremiumScraper {
    constructor() {
        this.currentTaskId = null;
        this.progressInterval = null;
        this.isScrapingActive = false;
        this.results = [];
        
        this.initializeElements();
        this.setupEventListeners();
        this.loadSettings();
        this.initializeTheme();
    }

    initializeElements() {
        // Main controls
        this.elements = {
            // Input
            postUrls: document.getElementById('post-urls'),
            urlCount: document.getElementById('url-count'),
            scrapeBtn: document.getElementById('scrape-btn'),
            stopBtn: document.getElementById('stop-btn'),
            
            // Progress
            progressSection: document.getElementById('progress-section'),
            progressBar: document.getElementById('progress-bar'),
            progressText: document.getElementById('progress-text'),
            progressPercentage: document.getElementById('progress-percentage'),
            successRate: document.getElementById('success-rate'),
            failedCount: document.getElementById('failed-count'),
            elapsedTime: document.getElementById('elapsed-time'),
            remainingTime: document.getElementById('remaining-time'),
            mediaFound: document.getElementById('media-found'),
            mediaDownloaded: document.getElementById('media-downloaded'),
            currentActivity: document.getElementById('current-activity'),
            currentUrl: document.getElementById('current-url'),
            taskId: document.getElementById('task-id'),
            
            // Results
            resultsSection: document.getElementById('results-section'),
            resultsContainer: document.getElementById('results-container'),
            resultCount: document.getElementById('result-count'),
            saveTxtBtn: document.getElementById('save-txt-btn'),
            saveCsvBtn: document.getElementById('save-csv-btn'),
            saveJsonBtn: document.getElementById('save-json-btn'),
            openFolderBtn: document.getElementById('open-folder-btn'),
            
            // Settings
            themeToggle: document.getElementById('theme-toggle'),
            settingsBtn: document.getElementById('settings-btn'),
            settingsModal: document.getElementById('settings-modal'),
            closeSettings: document.getElementById('close-settings'),
            
            // Settings controls
            maxWorkers: document.getElementById('max-workers'),
            maxWorkersValue: document.getElementById('max-workers-value'),
            rateLimitMin: document.getElementById('rate-limit-min'),
            rateLimitMax: document.getElementById('rate-limit-max'),
            extractContent: document.getElementById('extract-content'),
            extractHashtags: document.getElementById('extract-hashtags'),
            extractMentions: document.getElementById('extract-mentions'),
            previewWords: document.getElementById('preview-words'),
            downloadMedia: document.getElementById('download-media'),
            createThumbnails: document.getElementById('create-thumbnails'),
            organizeByDate: document.getElementById('organize-by-date'),
            mediaQuality: document.getElementById('media-quality'),
            maxFileSize: document.getElementById('max-file-size'),
            maxFileSizeValue: document.getElementById('max-file-size-value'),
            resetSettings: document.getElementById('reset-settings'),
            saveSettings: document.getElementById('save-settings'),
            
            // Modals
            contentModal: document.getElementById('content-modal'),
            closeContentModal: document.getElementById('close-content-modal'),
            modalTitle: document.getElementById('modal-title'),
            modalContent: document.getElementById('modal-content')
        };
    }

    setupEventListeners() {
        // URL input
        this.elements.postUrls.addEventListener('input', () => this.updateUrlCount());
        
        // Main controls
        this.elements.scrapeBtn.addEventListener('click', () => this.startScraping());
        this.elements.stopBtn.addEventListener('click', () => this.stopScraping());
        
        // Save buttons
        this.elements.saveTxtBtn.addEventListener('click', () => this.saveResults('txt'));
        this.elements.saveCsvBtn.addEventListener('click', () => this.saveResults('csv'));
        this.elements.saveJsonBtn.addEventListener('click', () => this.saveResults('json'));
        this.elements.openFolderBtn.addEventListener('click', () => this.openDownloadFolder());
        
        // Theme toggle
        this.elements.themeToggle.addEventListener('click', () => this.toggleTheme());
        
        // Settings modal
        this.elements.settingsBtn.addEventListener('click', () => this.openSettings());
        this.elements.closeSettings.addEventListener('click', () => this.closeSettings());
        this.elements.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.elements.settingsModal) this.closeSettings();
        });
        
        // Settings controls
        this.elements.maxWorkers.addEventListener('input', () => {
            this.elements.maxWorkersValue.textContent = this.elements.maxWorkers.value;
        });
        
        this.elements.maxFileSize.addEventListener('input', () => {
            this.elements.maxFileSizeValue.textContent = this.elements.maxFileSize.value + 'MB';
        });
        
        this.elements.resetSettings.addEventListener('click', () => this.resetSettings());
        this.elements.saveSettings.addEventListener('click', () => this.saveSettingsToStorage());
        
        // Content modal
        this.elements.closeContentModal.addEventListener('click', () => this.closeContentModal());
        this.elements.contentModal.addEventListener('click', (e) => {
            if (e.target === this.elements.contentModal) this.closeContentModal();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeSettings();
                this.closeContentModal();
            }
        });
    }

    updateUrlCount() {
        const urls = this.elements.postUrls.value.trim();
        const urlList = urls ? urls.split('\n').filter(url => url.trim()) : [];
        this.elements.urlCount.textContent = urlList.length;
    }

    async startScraping() {
        const urls = this.elements.postUrls.value.trim();
        
        if (!urls) {
            this.showNotification('Vui lòng nhập ít nhất một URL Facebook', 'error');
            return;
        }
        
        const urlList = urls.split('\n').filter(url => url.trim());
        
        if (urlList.length === 0) {
            this.showNotification('Không tìm thấy URL hợp lệ', 'error');
            return;
        }

        // Get settings
        const config = this.getScrapingConfig();

        try {
            // Start scraping via API
            const response = await window.pywebview.api.start_premium_scraping(urlList, config);
            
            if (response.success) {
                this.currentTaskId = response.task_id;
                this.isScrapingActive = true;
                
                // Update UI
                this.elements.scrapeBtn.classList.add('hidden');
                this.elements.stopBtn.classList.remove('hidden');
                this.elements.progressSection.classList.remove('hidden');
                this.elements.resultsSection.classList.add('hidden');
                this.elements.taskId.textContent = `Task: ${this.currentTaskId}`;
                
                // Clear previous results
                this.elements.resultsContainer.innerHTML = '';
                this.results = [];
                
                // Start progress monitoring
                this.startProgressMonitoring();
                
                this.showNotification(`Bắt đầu scraping ${urlList.length} posts với ${config.max_workers} workers`, 'success');
            } else {
                this.showNotification(response.error, 'error');
            }
        } catch (error) {
            this.showNotification('Lỗi khi bắt đầu scraping: ' + error.message, 'error');
        }
    }

    async stopScraping() {
        try {
            const response = await window.pywebview.api.stop_premium_scraping();
            
            if (response.success) {
                this.isScrapingActive = false;
                this.stopProgressMonitoring();
                
                // Update UI
                this.elements.scrapeBtn.classList.remove('hidden');
                this.elements.stopBtn.classList.add('hidden');
                
                this.showNotification(response.message, 'info');
            } else {
                this.showNotification(response.error, 'error');
            }
        } catch (error) {
            this.showNotification('Lỗi khi dừng scraping: ' + error.message, 'error');
        }
    }

    startProgressMonitoring() {
        this.progressInterval = setInterval(async () => {
            try {
                const progress = await window.pywebview.api.get_premium_progress();
                this.updateProgressUI(progress);
                
                if (!progress.is_scraping && this.isScrapingActive) {
                    // Scraping completed
                    this.isScrapingActive = false;
                    this.stopProgressMonitoring();
                    
                    // Update UI
                    this.elements.scrapeBtn.classList.remove('hidden');
                    this.elements.stopBtn.classList.add('hidden');
                    
                    // Load results
                    await this.loadResults();
                    
                    this.showNotification('Scraping hoàn thành!', 'success');
                }
            } catch (error) {
                console.error('Error monitoring progress:', error);
            }
        }, 1000);
    }

    stopProgressMonitoring() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    updateProgressUI(progressData) {
        const progress = progressData.progress;
        const percentage = progress.total_tasks > 0 ? 
            Math.round((progress.completed_tasks / progress.total_tasks) * 100) : 0;
        
        // Main progress
        this.elements.progressBar.style.width = percentage + '%';
        this.elements.progressText.textContent = `${progress.completed_tasks} / ${progress.total_tasks} posts hoàn thành`;
        this.elements.progressPercentage.textContent = percentage + '%';
        
        // Detailed stats
        this.elements.successRate.textContent = progress.success_rate.toFixed(1) + '%';
        this.elements.failedCount.textContent = progress.failed_tasks;
        this.elements.elapsedTime.textContent = progress.elapsed_time.toFixed(1) + 's';
        this.elements.remainingTime.textContent = progress.estimated_remaining.toFixed(1) + 's';
        this.elements.mediaFound.textContent = progress.media_found || 0;
        this.elements.mediaDownloaded.textContent = progress.media_downloaded || 0;
        
        // Current activity
        this.elements.currentActivity.textContent = progress.current_activity || 'Đang xử lý...';
        this.elements.currentUrl.textContent = progress.current_url ? 
            progress.current_url.substring(0, 60) + '...' : '';
    }

    async loadResults() {
        try {
            const response = await window.pywebview.api.get_premium_results();
            
            if (response.success) {
                this.results = response.results;
                this.displayResults(this.results);
                this.elements.resultCount.textContent = `${response.total_count} posts đã xử lý`;
                this.elements.resultsSection.classList.remove('hidden');
            } else {
                this.showNotification(response.error || 'Không thể tải kết quả', 'error');
            }
        } catch (error) {
            this.showNotification('Lỗi khi tải kết quả: ' + error.message, 'error');
        }
    }

    displayResults(results) {
        this.elements.resultsContainer.innerHTML = '';
        
        results.forEach((result, index) => {
            const card = this.createPostCard(result, index);
            this.elements.resultsContainer.appendChild(card);
        });
    }

    createPostCard(result, index) {
        const card = document.createElement('div');
        card.className = 'post-card bg-white/80 dark:bg-gray-800/80 backdrop-blur-md rounded-2xl shadow-lg p-6 border border-white/20 dark:border-gray-700/30 fade-in';
        
        if (!result.success || result.error_message) {
            card.innerHTML = this.createErrorCard(result);
        } else {
            card.innerHTML = this.createSuccessCard(result);
        }
        
        return card;
    }

    createErrorCard(result) {
        return `
            <div class="flex items-start space-x-4">
                <div class="flex-shrink-0 w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-xl flex items-center justify-center">
                    <i class="fas fa-exclamation-triangle text-red-500 text-lg"></i>
                </div>
                <div class="flex-grow">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-200 mb-2">Lỗi Xử Lý Post</h3>
                    <p class="text-red-600 dark:text-red-400 mb-3">${result.error_message || 'Lỗi không xác định'}</p>
                    <div class="text-sm text-gray-500 dark:text-gray-400 space-y-1">
                        <p><strong>URL:</strong> <span class="break-all">${result.url}</span></p>
                        <p><strong>Thời gian xử lý:</strong> ${(result.processing_time || 0).toFixed(2)}s</p>
                    </div>
                </div>
            </div>
        `;
    }

    createSuccessCard(result) {
        const data = result.post_data;
        const hasContent = data.content && data.content.full_text;
        const hasMedia = data.media_items && data.media_items.length > 0;
        
        return `
            <div class="space-y-6">
                <!-- Header -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                            <i class="fas fa-user text-white text-lg"></i>
                        </div>
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-200">${data.user_name || 'Người dùng không xác định'}</h3>
                            <div class="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
                                <span class="px-2 py-1 bg-${this.getPostTypeColor(data.post_type)}-100 dark:bg-${this.getPostTypeColor(data.post_type)}-900/30 text-${this.getPostTypeColor(data.post_type)}-700 dark:text-${this.getPostTypeColor(data.post_type)}-400 rounded-lg">
                                    ${this.getPostTypeIcon(data.post_type)} ${this.getPostTypeName(data.post_type)}
                                </span>
                                <span>•</span>
                                <span>${(result.processing_time || 0).toFixed(2)}s</span>
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center space-x-2">
                        ${data.local_folder ? `
                            <button onclick="premiumScraper.openPostFolder('${data.local_folder}')" class="p-2 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 transition-colors" title="Mở thư mục">
                                <i class="fas fa-folder-open"></i>
                            </button>
                        ` : ''}
                        <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                    </div>
                </div>

                <!-- Content Preview -->
                ${hasContent ? this.createContentPreview(data.content) : ''}

                <!-- Media Preview -->
                ${hasMedia ? this.createMediaPreview(data.media_items, result.task_id) : ''}

                <!-- Stats -->
                <div class="grid grid-cols-3 gap-4">
                    <div class="text-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                        <div class="flex items-center justify-center space-x-1 mb-1">
                            <i class="fas fa-thumbs-up text-blue-500"></i>
                            <span class="text-sm text-gray-500 dark:text-gray-400">Likes</span>
                        </div>
                        <p class="text-lg font-semibold text-gray-900 dark:text-gray-200">${data.stats?.likes || '0'}</p>
                    </div>
                    <div class="text-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                        <div class="flex items-center justify-center space-x-1 mb-1">
                            <i class="fas fa-comment text-yellow-500"></i>
                            <span class="text-sm text-gray-500 dark:text-gray-400">Comments</span>
                        </div>
                        <p class="text-lg font-semibold text-gray-900 dark:text-gray-200">${data.stats?.comments || '0'}</p>
                    </div>
                    <div class="text-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-xl">
                        <div class="flex items-center justify-center space-x-1 mb-1">
                            <i class="fas fa-share text-purple-500"></i>
                            <span class="text-sm text-gray-500 dark:text-gray-400">Shares</span>
                        </div>
                        <p class="text-lg font-semibold text-gray-900 dark:text-gray-200">${data.stats?.shares || '0'}</p>
                    </div>
                </div>

                <!-- Footer -->
                <div class="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-600">
                    <div class="text-sm text-gray-500 dark:text-gray-400">
                        <span class="break-all">${data.original_url}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button onclick="premiumScraper.copyPostSummary(${result.task_id})" class="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                            <i class="fas fa-copy mr-1"></i>Copy
                        </button>
                        ${hasMedia ? `
                            <span class="text-sm text-gray-500 dark:text-gray-400">
                                ${result.media_downloaded || 0}/${data.media_count || 0} media tải thành công
                            </span>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }

    createContentPreview(content) {
        if (!content || !content.full_text) return '';
        
        const showPreview = content.has_more;
        const displayText = showPreview ? content.preview_text : content.full_text;
        
        return `
            <div class="content-preview bg-gray-50 dark:bg-gray-700/30 rounded-xl p-4 ${showPreview ? 'max-h-32' : ''}">
                <div class="prose dark:prose-invert max-w-none">
                    <p class="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">${this.escapeHtml(displayText)}</p>
                </div>
                ${showPreview ? `
                    <div class="content-fade"></div>
                    <button onclick="premiumScraper.showFullContent('${content.full_text}', '${content.word_count} từ')" class="mt-3 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium text-sm transition-colors">
                        <i class="fas fa-expand-alt mr-1"></i>Xem toàn bộ (${content.word_count} từ)
                    </button>
                ` : ''}
                ${content.hashtags && content.hashtags.length > 0 ? `
                    <div class="mt-3 flex flex-wrap gap-1">
                        ${content.hashtags.map(tag => `<span class="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-xs rounded-lg">${tag}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    createMediaPreview(mediaItems, taskId) {
        if (!mediaItems || mediaItems.length === 0) return '';
        
        const images = mediaItems.filter(item => item.type === 'image');
        const videos = mediaItems.filter(item => item.type === 'video');
        const showCount = Math.min(4, images.length);
        const remainingCount = Math.max(0, images.length - showCount);
        
        return `
            <div class="media-preview-container">
                <div class="flex items-center justify-between mb-3">
                    <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center">
                        <i class="fas fa-images text-purple-500 mr-2"></i>
                        Media (${images.length} ảnh, ${videos.length} video)
                    </h4>
                    ${mediaItems.length > 4 ? `
                        <button onclick="premiumScraper.showAllMedia(${taskId})" class="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium">
                            Xem tất cả
                        </button>
                    ` : ''}
                </div>
                
                <div class="media-grid">
                    ${images.slice(0, showCount).map((item, index) => `
                        <div class="media-item" onclick="premiumScraper.showMediaGallery(${taskId}, ${index})">
                            <img src="${item.url}" alt="Media ${index + 1}" loading="lazy" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIGZpbGw9Im5vbmUiIHN0cm9rZT0iY3VycmVudENvbG9yIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIgY2xhc3M9ImZlYXRoZXIgZmVhdGhlci1pbWFnZSI+PHJlY3QgeD0iMyIgeT0iMyIgd2lkdGg9IjE4IiBoZWlnaHQ9IjE4IiByeD0iMiIgcnk9IjIiLz48Y2lyY2xlIGN4PSI4LjUiIGN5PSI4LjUiIHI9IjEuNSIvPjxwYXRoIGQ9Im0yMSAxNS00LTQtNSA1Ii8+PC9zdmc+'">
                            <div class="media-fade-overlay"></div>
                            ${index === showCount - 1 && remainingCount > 0 ? `
                                <div class="media-count-badge">+${remainingCount}</div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
                
                ${videos.length > 0 ? `
                    <div class="mt-3 p-3 bg-gray-50 dark:bg-gray-700/30 rounded-lg">
                        <div class="flex items-center text-sm text-gray-600 dark:text-gray-400">
                            <i class="fas fa-video text-red-500 mr-2"></i>
                            <span>${videos.length} video(s) được tìm thấy</span>
                            <button onclick="premiumScraper.showVideoList(${taskId})" class="ml-auto text-blue-600 dark:text-blue-400 hover:underline">
                                Xem danh sách
                            </button>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    // Modal functions
    showFullContent(fullText, wordCount) {
        this.elements.modalTitle.textContent = `Nội dung đầy đủ (${wordCount})`;
        this.elements.modalContent.innerHTML = `
            <div class="prose dark:prose-invert max-w-none">
                <p class="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">${this.escapeHtml(fullText)}</p>
            </div>
        `;
        this.elements.contentModal.classList.remove('hidden');
    }

    showAllMedia(taskId) {
        const result = this.results.find(r => r.task_id === taskId);
        if (!result || !result.post_data.media_items) return;
        
        const mediaItems = result.post_data.media_items;
        this.elements.modalTitle.textContent = `Tất cả Media (${mediaItems.length})`;
        
        const mediaGrid = mediaItems.map((item, index) => `
            <div class="media-item cursor-pointer" onclick="premiumScraper.showMediaGallery(${taskId}, ${index})">
                <img src="${item.url}" alt="Media ${index + 1}" class="w-full h-32 object-cover rounded-lg" loading="lazy">
                <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <div>${item.type.toUpperCase()}</div>
                    ${item.filename ? `<div>${item.filename}</div>` : ''}
                    ${item.size_bytes ? `<div>${(item.size_bytes / 1024 / 1024).toFixed(2)} MB</div>` : ''}
                </div>
            </div>
        `).join('');
        
        this.elements.modalContent.innerHTML = `
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                ${mediaGrid}
            </div>
        `;
        this.elements.contentModal.classList.remove('hidden');
    }

    showMediaGallery(taskId, startIndex = 0) {
        const result = this.results.find(r => r.task_id === taskId);
        if (!result || !result.post_data.media_items) return;
        
        const mediaItems = result.post_data.media_items.filter(item => item.type === 'image');
        if (mediaItems.length === 0) return;
        
        this.elements.modalTitle.textContent = `Thư viện ảnh (${startIndex + 1}/${mediaItems.length})`;
        
        const currentItem = mediaItems[startIndex];
        this.elements.modalContent.innerHTML = `
            <div class="text-center">
                <div class="relative inline-block">
                    <img src="${currentItem.url}" alt="Image ${startIndex + 1}" class="max-w-full max-h-96 rounded-lg shadow-lg" loading="lazy">
                    <div class="absolute bottom-4 left-4 bg-black/70 text-white px-3 py-1 rounded-lg text-sm">
                        ${startIndex + 1} / ${mediaItems.length}
                    </div>
                </div>
                
                <div class="flex justify-center space-x-4 mt-6">
                    ${startIndex > 0 ? `
                        <button onclick="premiumScraper.showMediaGallery(${taskId}, ${startIndex - 1})" class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors">
                            <i class="fas fa-chevron-left mr-2"></i>Trước
                        </button>
                    ` : ''}
                    ${startIndex < mediaItems.length - 1 ? `
                        <button onclick="premiumScraper.showMediaGallery(${taskId}, ${startIndex + 1})" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                            Sau<i class="fas fa-chevron-right ml-2"></i>
                        </button>
                    ` : ''}
                </div>
                
                ${currentItem.local_path ? `
                    <div class="mt-4 p-3 bg-green-50 dark:bg-green-900/30 rounded-lg">
                        <div class="flex items-center justify-center space-x-2 text-green-700 dark:text-green-400">
                            <i class="fas fa-download"></i>
                            <span class="text-sm">Đã tải xuống: ${currentItem.filename}</span>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
        this.elements.contentModal.classList.remove('hidden');
    }

    closeContentModal() {
        this.elements.contentModal.classList.add('hidden');
    }

    // Utility functions
    getPostTypeColor(postType) {
        const colors = {
            'text': 'gray',
            'image': 'blue',
            'video': 'red',
            'mixed': 'purple',
            'link': 'green',
            'unknown': 'gray'
        };
        return colors[postType] || 'gray';
    }

    getPostTypeIcon(postType) {
        const icons = {
            'text': '📝',
            'image': '🖼️',
            'video': '🎥',
            'mixed': '🎭',
            'link': '🔗',
            'unknown': '❓'
        };
        return icons[postType] || '❓';
    }

    getPostTypeName(postType) {
        const names = {
            'text': 'Text Post',
            'image': 'Image Post',
            'video': 'Video Post',
            'mixed': 'Mixed Media',
            'link': 'Link Post',
            'unknown': 'Unknown'
        };
        return names[postType] || 'Unknown';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Settings functions
    getScrapingConfig() {
        return {
            max_workers: parseInt(this.elements.maxWorkers.value),
            driver_pool_size: parseInt(this.elements.maxWorkers.value),
            rate_limit_min: parseFloat(this.elements.rateLimitMin.value),
            rate_limit_max: parseFloat(this.elements.rateLimitMax.value),
            extract_content: this.elements.extractContent.checked,
            extract_hashtags: this.elements.extractHashtags.checked,
            extract_mentions: this.elements.extractMentions.checked,
            content_preview_words: parseInt(this.elements.previewWords.value),
            download_media: this.elements.downloadMedia.checked,
            create_thumbnails: this.elements.createThumbnails.checked,
            organize_by_date: this.elements.organizeByDate.checked,
            media_quality: this.elements.mediaQuality.value,
            max_media_size_mb: parseInt(this.elements.maxFileSize.value)
        };
    }

    openSettings() {
        this.elements.settingsModal.classList.remove('hidden');
    }

    closeSettings() {
        this.elements.settingsModal.classList.add('hidden');
    }

    resetSettings() {
        this.elements.maxWorkers.value = 3;
        this.elements.maxWorkersValue.textContent = '3';
        this.elements.rateLimitMin.value = 2;
        this.elements.rateLimitMax.value = 5;
        this.elements.extractContent.checked = true;
        this.elements.extractHashtags.checked = true;
        this.elements.extractMentions.checked = true;
        this.elements.previewWords.value = 50;
        this.elements.downloadMedia.checked = true;
        this.elements.createThumbnails.checked = true;
        this.elements.organizeByDate.checked = true;
        this.elements.mediaQuality.value = 'high';
        this.elements.maxFileSize.value = 50;
        this.elements.maxFileSizeValue.textContent = '50MB';
    }

    saveSettingsToStorage() {
        const settings = this.getScrapingConfig();
        localStorage.setItem('premiumScraperSettings', JSON.stringify(settings));
        this.closeSettings();
        this.showNotification('Cài đặt đã được lưu', 'success');
    }

    loadSettings() {
        const savedSettings = localStorage.getItem('premiumScraperSettings');
        if (savedSettings) {
            try {
                const settings = JSON.parse(savedSettings);
                
                this.elements.maxWorkers.value = settings.max_workers || 3;
                this.elements.maxWorkersValue.textContent = settings.max_workers || 3;
                this.elements.rateLimitMin.value = settings.rate_limit_min || 2;
                this.elements.rateLimitMax.value = settings.rate_limit_max || 5;
                this.elements.extractContent.checked = settings.extract_content !== false;
                this.elements.extractHashtags.checked = settings.extract_hashtags !== false;
                this.elements.extractMentions.checked = settings.extract_mentions !== false;
                this.elements.previewWords.value = settings.content_preview_words || 50;
                this.elements.downloadMedia.checked = settings.download_media !== false;
                this.elements.createThumbnails.checked = settings.create_thumbnails !== false;
                this.elements.organizeByDate.checked = settings.organize_by_date !== false;
                this.elements.mediaQuality.value = settings.media_quality || 'high';
                this.elements.maxFileSize.value = settings.max_media_size_mb || 50;
                this.elements.maxFileSizeValue.textContent = (settings.max_media_size_mb || 50) + 'MB';
            } catch (error) {
                console.error('Error loading settings:', error);
            }
        }
    }

    // Theme functions
    initializeTheme() {
        const html = document.documentElement;
        
        if (localStorage.getItem('theme') === 'dark' || 
            (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            html.classList.add('dark');
        } else {
            html.classList.remove('dark');
        }
    }

    toggleTheme() {
        const html = document.documentElement;
        html.classList.toggle('dark');
        localStorage.setItem('theme', html.classList.contains('dark') ? 'dark' : 'light');
    }

    // Save functions
    async saveResults(format) {
        try {
            const response = await window.pywebview.api.save_premium_results(format);
            
            if (response.success) {
                this.showNotification(`Đã lưu ${response.count} kết quả dưới định dạng ${format.toUpperCase()}`, 'success');
            } else {
                this.showNotification(response.error, 'error');
            }
        } catch (error) {
            this.showNotification('Lỗi khi lưu kết quả: ' + error.message, 'error');
        }
    }

    async openDownloadFolder() {
        try {
            const response = await window.pywebview.api.open_download_folder();
            if (!response.success) {
                this.showNotification(response.error, 'error');
            }
        } catch (error) {
            this.showNotification('Không thể mở thư mục: ' + error.message, 'error');
        }
    }

    async openPostFolder(folderPath) {
        try {
            const response = await window.pywebview.api.open_post_folder(folderPath);
            if (!response.success) {
                this.showNotification(response.error, 'error');
            }
        } catch (error) {
            this.showNotification('Không thể mở thư mục: ' + error.message, 'error');
        }
    }

    copyPostSummary(taskId) {
        const result = this.results.find(r => r.task_id === taskId);
        if (!result) return;
        
        const data = result.post_data;
        const summary = `Bài viết của ${data.user_name || 'Unknown'}
        (${data.stats?.likes || '0'} lượt quan tâm, ${data.stats?.comments || '0'} lượt bình luận, ${data.stats?.shares || '0'} lượt chia sẻ)
        
${data.content?.full_text || 'Không có nội dung'}

URL: ${data.original_url}`;
        
        navigator.clipboard.writeText(summary).then(() => {
            this.showNotification('Đã copy thông tin post', 'success');
        }).catch(() => {
            this.showNotification('Không thể copy', 'error');
        });
    }

    // Notification system
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            info: 'bg-blue-500 text-white',
            warning: 'bg-yellow-500 text-black'
        };
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle',
            warning: 'fas fa-exclamation-triangle'
        };
        
        notification.className = `fixed top-6 right-6 z-50 px-6 py-4 rounded-xl shadow-lg ${colors[type]} fade-in max-w-md`;
        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="${icons[type]}"></i>
                <span class="font-medium">${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.premiumScraper = new PremiumScraper();
}); 