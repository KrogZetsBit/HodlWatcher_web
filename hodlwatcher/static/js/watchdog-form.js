document.addEventListener('DOMContentLoaded', function() {
    // Obtener referencias a los campos del formulario
    const sideSelect = document.getElementById('id_side');
    const currencySelect = document.getElementById('id_currency');
    const paymentMethodSelect = document.getElementById('id_payment_method_id');
    const assetCodeSelect = document.getElementById('id_asset_code');
    const amountInput = document.getElementById('id_amount');
    const rateFeeInput = document.getElementById('id_rate_fee');

    // Mapeo de códigos de moneda a códigos de país para las banderas
    const currencyToCountryCode = {
        'AFN': 'af', // Afganistán
        'ARS': 'ar', // Argentina
        'AUD': 'au', // Australia
        'THB': 'th', // Tailandia
        'PAB': 'pa', // Panamá
        'BYN': 'by', // Bielorrusia
        'BOB': 'bo', // Bolivia
        'BRL': 'br', // Brasil
        'XOF': 'sn', // Senegal (como representante de BCEAO)
        'CAD': 'ca', // Canadá
        'CLP': 'cl', // Chile
        'COP': 'co', // Colombia
        'CRC': 'cr', // Costa Rica
        'CZK': 'cz', // República Checa
        'DKK': 'dk', // Dinamarca
        'DOP': 'do', // República Dominicana
        'VND': 'vn', // Vietnam
        'EGP': 'eg', // Egipto
        'ETB': 'et', // Etiopía
        'EUR': 'eu', // Unión Europea
        'HUF': 'hu', // Hungría
        'PYG': 'py', // Paraguay
        'UAH': 'ua', // Ucrania
        'ISK': 'is', // Islandia
        'INR': 'in', // India
        'KES': 'ke', // Kenia
        'KWD': 'kw', // Kuwait
        'GEL': 'ge', // Georgia
        'MYR': 'my', // Malasia
        'MXN': 'mx', // México
        'NGN': 'ng', // Nigeria
        'ILS': 'il', // Israel
        'RON': 'ro', // Rumanía
        'TWD': 'tw', // Taiwán
        'NZD': 'nz', // Nueva Zelanda
        'PEN': 'pe', // Perú
        'PKR': 'pk', // Pakistán
        'UYU': 'uy', // Uruguay
        'PHP': 'ph', // Filipinas
        'GBP': 'gb', // Reino Unido
        'ZAR': 'za', // Sudáfrica
        'KHR': 'kh', // Camboya
        'IDR': 'id', // Indonesia
        'RUB': 'ru', // Rusia
        'SGD': 'sg', // Singapur
        'KRW': 'kr', // Corea del Sur
        'LKR': 'lk', // Sri Lanka
        'SEK': 'se', // Suecia
        'CHF': 'ch', // Suiza
        'BDT': 'bd', // Bangladesh
        'USDT': 'us', // Estados Unidos (Tether)
        'TRY': 'tr', // Turquía
        'AED': 'ae', // Emiratos Árabes Unidos
        'USD': 'us', // Estados Unidos
        'USDC': 'us', // Estados Unidos (USD Coin)
        'VES': 've', // Venezuela
        'JPY': 'jp', // Japón
        'CNY': 'cn', // China
        'PLN': 'pl'  // Polonia
    };

    // Función para actualizar el resumen
    function updateSummary() {
        // Obtiene valores de los campos
        const side = sideSelect ? sideSelect.options[sideSelect.selectedIndex]?.text || '' : '';
        const currencyCode = currencySelect ? currencySelect.value || '' : '';
        const paymentMethod = paymentMethodSelect ? paymentMethodSelect.options[paymentMethodSelect.selectedIndex]?.text || '' : '';
        const assetCode = assetCodeSelect ? assetCodeSelect.value || '' : '';
        const amount = amountInput ? amountInput.value || '0' : '0';
        const rateFee = rateFeeInput ? rateFeeInput.value || '0' : '0';

        // Actualiza textos en el resumen
        updateElementText('.summary-side', side);
        updateElementText('.summary-asset', assetCode);
        updateElementText('.summary-currency', currencyCode);
        updateElementText('.summary-payment-method', paymentMethod);
        updateElementText('.summary-amount', amount);
        updateElementText('.summary-rate-fee', rateFee + '%');

        // Actualiza iconos y clases del badge
        const sideBadge = document.querySelector('.side-badge');
        if (sideBadge) {
            // Eliminar clases existentes
            sideBadge.classList.remove('bg-danger', 'bg-success', 'text-danger', 'text-success', 'border-danger', 'border-success');

            // Agregar clases según el valor seleccionado
            if (side === 'Buy') {
                sideBadge.classList.add('bg-danger', 'text-danger', 'border-danger');
            } else {
                sideBadge.classList.add('bg-success', 'text-success', 'border-success');
            }
        }

        // Actualiza el icono de flecha
        const sideIcon = document.querySelector('.side-icon');
        if (sideIcon) {
            sideIcon.classList.remove('bi-arrow-down-circle', 'bi-arrow-up-circle');
            sideIcon.classList.add(side === 'Buy' ? 'bi-arrow-down-circle' : 'bi-arrow-up-circle');
        }

        // Actualiza la bandera de la moneda usando el mapeo
        const currencyFlag = document.querySelector('.currency-flag');
        if (currencyFlag && currencyCode) {
            // Obtener el código de país correcto o usar 'un' (Naciones Unidas) como fallback
            const countryCode = currencyToCountryCode[currencyCode] || 'un';

            // Reemplazar todas las clases existentes que comiencen con "fi-"
            const classNames = currencyFlag.className.split(' ');
            const newClassNames = classNames.filter(className => !className.startsWith('fi-'));
            newClassNames.push(`fi-${countryCode}`);
            currencyFlag.className = newClassNames.join(' ');
        }

        // Actualizar la frase dinámica
        updateDynamicPhrase();
    }

    // Función auxiliar para actualizar texto de elementos
    function updateElementText(selector, text) {
        const element = document.querySelector(selector);
        if (element) {
            element.textContent = text;
        }
    }

    // Función para actualizar la frase dinámica
    function updateDynamicPhrase() {
        // Obtener los valores actuales del resumen
        const side = document.querySelector('.summary-side').textContent.toLowerCase();
        const sideText = side === 'buy' ? 'sell' : 'buy';

        // Actualizar elementos de la frase
        document.getElementById('phrase-side').textContent = sideText;
        document.getElementById('phrase-amount').textContent = document.querySelector('.summary-amount').textContent;
        document.getElementById('phrase-currency').textContent = document.querySelector('.summary-currency').textContent;
        document.getElementById('phrase-asset').textContent = document.querySelector('.summary-asset').textContent;
        document.getElementById('phrase-payment-method').textContent = document.querySelector('.summary-payment-method').textContent;
        document.getElementById('phrase-rate-fee').textContent = document.querySelector('.summary-rate-fee').textContent;
    }

    // Agregar event listeners para los cambios en los campos
    const formFields = [sideSelect, currencySelect, paymentMethodSelect, assetCodeSelect, amountInput, rateFeeInput];
    formFields.forEach(field => {
        if (field) {
            field.addEventListener('change', updateSummary);
        }
    });

    // Inicializar el resumen con los valores actuales
    updateSummary();
});
