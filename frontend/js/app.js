// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// State Management
let currentPage = 'home';

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    showHome();
});

// Navigation
function showHome() {
    console.log("show home")
    loadStats();
    currentPage = 'home';
    updateActiveNav('home');
    hideAllPages();
    document.getElementById('home-page').style.display = 'block';
    loadPosts();
}

function showRanking() {
    console.log("show ranking")
    loadStats();
    currentPage = 'ranking';
    updateActiveNav('ranking');
    hideAllPages();
    document.getElementById('ranking-page').style.display = 'block';
    loadRanking();
}

function showPostDetail(slug) {
    console.log("show post detail")
    currentPage = 'detail';
    hideAllPages();
    document.getElementById('post-detail-page').style.display = 'block';
    loadPostDetail(slug);
}

function hideAllPages() {
    document.getElementById('home-page').style.display = 'none';
    document.getElementById('ranking-page').style.display = 'none';
    document.getElementById('post-detail-page').style.display = 'none';
    document.getElementById('empty-state').style.display = 'none';
}

function updateActiveNav(page) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-page') === page) {
            link.classList.add('active');
        }
    });
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// API Calls
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return null;
    }
}

// Load Stats
async function loadStats() {
    const posts = await fetchAPI('/posts/');
    const authors = await fetchAPI('/authors/');
    const ranking = await fetchAPI('/stats/top-posts?limit=50');

    if (posts) {
        document.getElementById('stat-posts').textContent = posts.length;
    }

    if (authors) {
        document.getElementById('stat-authors').textContent = authors.length;
    }

    if (ranking) {
        const totalViews = ranking.reduce((sum, post) => sum + post.views_count, 0);
        document.getElementById('stat-views').textContent = totalViews.toLocaleString('pt-BR');
    }
}

// Load Posts Grid
async function loadPosts() {
    showLoading();
    const container = document.getElementById('posts-grid');
    container.innerHTML = '';

    const posts = await fetchAPI('/posts/');
    hideLoading();

    if (!posts || posts.length === 0) {
        document.getElementById('empty-state').style.display = 'block';
        return;
    }

    posts.forEach(post => {
        const card = createPostCard(post);
        container.appendChild(card);
    });
}

function createPostCard(post) {
    const card = document.createElement('div');
    card.className = 'post-card';
    card.onclick = () => showPostDetail(post.slug);

    card.innerHTML = `
        <div class="post-header">
            <h3 class="post-title">${post.title}</h3>
            <p class="post-summary">${post.summary || 'Sem resumo disponível'}</p>
        </div>
        <div class="post-meta">
            <span class="post-author">👤 ${post.author_name}</span>
        </div>
    `;

    return card;
}

function getPostViews(post) {
    // Pega views do campo views_count se disponível, senão retorna 0
    return (post.views_count || 0).toLocaleString('pt-BR');
}

// Load Post Detail
async function loadPostDetail(slug) {
    showLoading();
    const container = document.getElementById('post-detail-content');
    container.innerHTML = '';

    // Incrementa view ao buscar o post
    const post = await fetchAPI(`/posts/slug/${slug}?increment_view=true`);
    hideLoading();

    if (!post) {
        container.innerHTML = '<p>Post não encontrado.</p>';
        return;
    }

    container.innerHTML = `
        <h1>${post.title}</h1>
        <div class="post-detail-meta">
            <div class="meta-item">
                <span>👤</span>
                <span>${post.author_name}</span>
            </div>
            <div class="meta-item">
                <span>📅</span>
                <span>${formatDate(post.created_at)}</span>
            </div>
            <div class="meta-item">
                <span>👁️</span>
                <span>${post.views_count.toLocaleString('pt-BR')} visualizações</span>
            </div>
        </div>
        <div class="post-content">
            ${formatContent(post.content)}
        </div>
    `;

    // Aplica syntax highlighting nos blocos de código
    document.querySelectorAll('.post-content pre code').forEach((block) => {
        hljs.highlightElement(block);
    });

    // Atualiza stats após incrementar view
    setTimeout(() => loadStats(), 500);
}

// Load Ranking
async function loadRanking() {
    showLoading();
    const container = document.getElementById('ranking-list');
    container.innerHTML = '';

    const ranking = await fetchAPI('/stats/top-posts?limit=10');
    hideLoading();

    if (!ranking || ranking.length === 0) {
        document.getElementById('empty-state').style.display = 'block';
        return;
    }

    ranking.forEach(post => {
        const item = createRankingItem(post);
        container.appendChild(item);
    });
}

function createRankingItem(post) {
    const item = document.createElement('div');
    item.className = 'ranking-item';
    item.onclick = () => showPostDetail(post.slug);

    const rankClass = post.rank <= 3 ? `top-${post.rank}` : '';

    item.innerHTML = `
        <div class="rank-badge ${rankClass}">#${post.rank}</div>
        <div class="ranking-content">
            <div class="ranking-title">${post.title}</div>
            <div class="ranking-author">Por ${post.author_name}</div>
        </div>
        <div class="ranking-views">${post.views_count.toLocaleString('pt-BR')}</div>
    `;

    return item;
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatContent(content) {
    // Renderiza Markdown para HTML
    return marked.parse(content);
}
