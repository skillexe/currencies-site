document.addEventListener('DOMContentLoaded', () => {
    // Инициализация элементов Materialize (если потребуется)
    M.AutoInit();

    // Загрузка сохранённой темы
    const body = document.body;
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-theme');
    }

    // Переключение темы
    document.getElementById('theme-toggle').addEventListener('click', () => {
        body.classList.toggle('dark-theme');
        localStorage.setItem('theme', body.classList.contains('dark-theme') ? 'dark' : 'light');
    });
});
