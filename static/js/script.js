document.addEventListener('DOMContentLoaded', function() {
    // Инициализация компонентов Materialize
    M.AutoInit();

    // Логика для переключения темы
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        body.classList.add('dark-theme');
    }

    themeToggle.addEventListener('click', () => {
        body.classList.toggle('dark-theme');
        localStorage.setItem('theme', body.classList.contains('dark-theme') ? 'dark' : 'light');
    });

    // Логика для переключения источников
    function updateActiveButton(activeButton) {
        document.querySelectorAll('.btn-source').forEach(btn => {
            btn.classList.remove('teal');
            btn.classList.add('grey');
        });
        activeButton.classList.remove('grey');
        activeButton.classList.add('teal');
    }

    document.getElementById('source-cbr').addEventListener('click', function() {
        loadRates('/api/rates');
        updateActiveButton(this);
    });

    document.getElementById('source-exchangerate').addEventListener('click', function() {
        loadRates('/api/rates_exchangerate');
        updateActiveButton(this);
    });

    function loadRates(apiEndpoint) {
        fetch(apiEndpoint)
            .then(response => response.json())
            .then(data => {
                const ratesTableBody = document.getElementById('rates-table').querySelector('tbody');
                ratesTableBody.innerHTML = '';
                data.data.forEach(rate => {
                    const row = `
                        <tr>
                            <td>${rate.code}</td>
                            <td>${rate.value.toFixed(2)}</td>
                        </tr>`;
                    ratesTableBody.innerHTML += row;
                });
            });
    }

    // Загрузка данных по умолчанию
    loadRates('/api/rates');
});
