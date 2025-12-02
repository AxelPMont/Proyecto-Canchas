// static/js/admin.js

document.addEventListener('DOMContentLoaded', () => {
    /* ===========================
       NAV ENTRE SECCIONES
       =========================== */
    const menuItems = document.querySelectorAll('.menu-item');
    const sections = document.querySelectorAll('.content-section');
    const topbarTitle = document.querySelector('.topbar-title h2');

    function showSection(sectionId) {
        // Ocultar todas
        sections.forEach(sec => sec.classList.remove('active'));

        const target = document.getElementById(sectionId);
        if (target) {
            target.classList.add('active');
            // Actualizar título
            if (topbarTitle) {
                // Buscar texto del menú correspondiente
                const menu = document.querySelector(`.menu-item[data-section="${sectionId}"]`);
                const title = menu ? menu.textContent.trim() : 'Dashboard';
                topbarTitle.textContent = title;
            }

            // Marcar menú activo
            menuItems.forEach(mi => mi.classList.remove('active'));
            const activeMenu = document.querySelector(`.menu-item[data-section="${sectionId}"]`);
            if (activeMenu) activeMenu.classList.add('active');
        }
    }

    menuItems.forEach(item => {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            const sectionId = this.getAttribute('data-section');
            if (sectionId) {
                showSection(sectionId);
                // Actualizar hash en la URL sin recargar
                history.replaceState(null, '', `#${sectionId}`);
            }
        });
    });

    // Si viene con hash (#matches, etc.), mostrar esa sección
    const initialHash = window.location.hash.replace('#', '');
    if (initialHash) {
        showSection(initialHash);
    }

    /* ===========================
       SIDEBAR RESPONSIVE (si lo usas)
       =========================== */
    window.toggleSidebar = function () {
        const sidebar = document.getElementById('adminSidebar');
        if (sidebar) sidebar.classList.toggle('show');
    };

    /* ===========================
       GENERADOR DE GRUPOS (DEMO)
       =========================== */
    window.generateGroups = function () {
        alert('Generando grupos aleatorios... (lógica pendiente en backend)');
    };

    /* ===========================
       DRAG & DROP FORMATIONS (DEMO)
       =========================== */
    let draggedElement = null;

    // Elementos arrastrables (todos los que tengan cursor: move en inline-style)
    document.querySelectorAll('[style*="cursor: move"]').forEach(element => {
        element.setAttribute('draggable', 'true');

        element.addEventListener('dragstart', function () {
            draggedElement = this;
            this.style.opacity = '0.5';
        });

        element.addEventListener('dragend', function () {
            this.style.opacity = '1';
        });
    });

    // Campo de juego (primer div con ese background de cancha)
    const field = Array.from(document.querySelectorAll('div')).find(div =>
        (div.style.background || '').includes('linear-gradient(180deg, #2e7d32')
    );

    if (field) {
        field.addEventListener('dragover', function (e) {
            e.preventDefault();
        });

        field.addEventListener('drop', function (e) {
            e.preventDefault();
            if (draggedElement) {
                const rect = this.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const playerMarker = document.createElement('div');
                playerMarker.style.position = 'absolute';
                playerMarker.style.left = x + 'px';
                playerMarker.style.top = y + 'px';
                playerMarker.style.transform = 'translate(-50%, -50%)';
                playerMarker.style.background = 'white';
                playerMarker.style.width = '50px';
                playerMarker.style.height = '50px';
                playerMarker.style.borderRadius = '50%';
                playerMarker.style.display = 'flex';
                playerMarker.style.alignItems = 'center';
                playerMarker.style.justifyContent = 'center';
                playerMarker.style.fontWeight = '700';
                playerMarker.style.cursor = 'move';
                playerMarker.style.boxShadow = '0 4px 8px rgba(0,0,0,0.3)';

                const strong = draggedElement.querySelector('strong');
                playerMarker.textContent = strong ? strong.textContent : 'J';

                this.appendChild(playerMarker);
            }
        });
    }

    /* ===========================
       ORDENAMIENTO TABLAS
       =========================== */
    document.querySelectorAll('.data-table th').forEach((th, index) => {
        th.style.cursor = 'pointer';
        th.addEventListener('click', function () {
            const table = this.closest('table');
            if (!table) return;
            const tbody = table.querySelector('tbody');
            if (!tbody) return;

            const rows = Array.from(tbody.querySelectorAll('tr'));

            const asc = !this.classList.contains('sorted-asc');
            // Reset clases de orden
            table.querySelectorAll('th').forEach(head => {
                head.classList.remove('sorted-asc', 'sorted-desc');
            });
            this.classList.add(asc ? 'sorted-asc' : 'sorted-desc');

            rows.sort((a, b) => {
                const aValue = (a.cells[index]?.textContent || '').trim();
                const bValue = (b.cells[index]?.textContent || '').trim();
                if (!isNaN(aValue) && !isNaN(bValue)) {
                    // numérico
                    return asc ? aValue - bValue : bValue - aValue;
                }
                return asc
                    ? aValue.localeCompare(bValue)
                    : bValue.localeCompare(aValue);
            });

            rows.forEach(row => tbody.appendChild(row));
        });
    });

    /* ===========================
       INDICADOR AUTO-SAVE (VISUAL)
       =========================== */
    let autoSaveTimeout;
    document.querySelectorAll('.form-control').forEach(input => {
        input.addEventListener('input', function () {
            clearTimeout(autoSaveTimeout);

            const label = this.previousElementSibling;
            if (!label || label.tagName !== 'LABEL') return;

            // Si ya hay indicador en ese label, no crear otro
            let saveIndicator = label.querySelector('.save-indicator');
            if (!saveIndicator) {
                saveIndicator = document.createElement('span');
                saveIndicator.className = 'save-indicator';
                saveIndicator.style.color = '#666';
                saveIndicator.style.fontSize = '0.85rem';
                saveIndicator.style.marginLeft = '0.5rem';
                label.appendChild(saveIndicator);
            }

            saveIndicator.textContent = 'Guardando...';
            saveIndicator.style.color = '#666';

            autoSaveTimeout = setTimeout(() => {
                if (saveIndicator && saveIndicator.parentElement) {
                    saveIndicator.textContent = '✓ Guardado';
                    saveIndicator.style.color = '#4caf50';

                    setTimeout(() => {
                        if (saveIndicator && saveIndicator.parentElement) {
                            saveIndicator.remove();
                        }
                    }, 2000);
                }
            }, 1500);
        });
    });

    /* ===========================
       CONFIRMAR ELIMINAR
       =========================== */
    document.querySelectorAll('.btn-danger').forEach(btn => {
        if (btn.textContent.includes('Eliminar')) {
            btn.addEventListener('click', function (e) {
                // Si es button dentro de form, el confirm se hace en onsubmit del form
                // Aquí manejamos casos sueltos
                if (!this.closest('form')) {
                    if (!confirm('¿Estás seguro de que deseas eliminar este elemento?')) {
                        e.preventDefault();
                    }
                }
            });
        }
    });
    // Manejar selección de plataforma
document.querySelectorAll('.platform-option input[type="radio"]').forEach(radio => {
  radio.addEventListener('change', function() {
    document.querySelectorAll('.platform-option').forEach(opt => opt.classList.remove('selected'));
    this.closest('.platform-option').classList.add('selected');
  });
});

// Manejar selección de estado
document.querySelectorAll('.status-option input[type="radio"]').forEach(radio => {
  radio.addEventListener('change', function() {
    document.querySelectorAll('.status-option').forEach(opt => opt.classList.remove('selected'));
    this.closest('.status-option').classList.add('selected');
  });
});

// Función para editar transmisión (placeholder)
function editTransmission(id) {
  alert('Editar transmisión #' + id + '\n\nFuncionalidad en desarrollo...');
}

// Validación del formulario
document.getElementById('transmissionForm')?.addEventListener('submit', function(e) {
  const url = document.querySelector('input[name="url_publica"]').value;
  if (url && !url.startsWith('http')) {
    e.preventDefault();
    alert('⚠️ La URL debe comenzar con http:// o https://');
    return false;
  }
});

window.openEditTransmissionModal = function(button) {
        const partidoId = button.getAttribute('data-partido-id');
        const plataforma = button.getAttribute('data-plataforma') || '';
        const url = button.getAttribute('data-url') || '';
        const estado = button.getAttribute('data-estado') || '';
        const camara = button.getAttribute('data-camara') || '';

        const modalEl = document.getElementById('editTransmissionModal');
        if (!modalEl) return;

        // Rellenar campos del modal
        const inputPartido = modalEl.querySelector('#edit_partido_id');
        const selectPlataforma = modalEl.querySelector('#edit_plataforma');
        const inputUrl = modalEl.querySelector('#edit_url_publica');
        const selectEstado = modalEl.querySelector('#edit_estado_transmision');
        const inputCamara = modalEl.querySelector('#edit_camara');

        if (inputPartido) inputPartido.value = partidoId || '';
        if (selectPlataforma && plataforma) selectPlataforma.value = plataforma;
        if (inputUrl) inputUrl.value = url;
        if (selectEstado && estado) selectEstado.value = estado;
        if (inputCamara) inputCamara.value = camara;

        // Mostrar modal (Bootstrap 5)
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    };

    window.openEditPublicationModal = function(button) {
        const pubId = button.getAttribute('data-pub-id');
        const titulo = button.getAttribute('data-titulo') || '';
        const categoria = button.getAttribute('data-categoria') || '';
        const contenido = button.getAttribute('data-contenido') || '';
        const estado = button.getAttribute('data-estado') || '';

        const modalEl = document.getElementById('editPublicationModal');
        if (!modalEl) return;

        const formEditPub = modalEl.querySelector('#formEditPublication');
        const inputPubId = modalEl.querySelector('#edit_pub_id');
        const inputTitulo = modalEl.querySelector('#edit_titulo');
        const selectCategoria = modalEl.querySelector('#edit_categoria');
        const textareaContenido = modalEl.querySelector('#edit_contenido');
        const selectEstado = modalEl.querySelector('#edit_estado');

        if (inputPubId) inputPubId.value = pubId || '';
        if (inputTitulo) inputTitulo.value = titulo;
        if (selectCategoria) selectCategoria.value = categoria;
        if (textareaContenido) textareaContenido.value = contenido;
        if (selectEstado) selectEstado.value = estado;

        // Actualizar action del form con el pub_id
        if (formEditPub) {
            formEditPub.action = `/admin/publicaciones/${pubId}/editar`;
        }

        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    };

    /* ===========================
       BUSCADOR EN TABLAS
       =========================== */
    function addTableSearch() {
        const tables = document.querySelectorAll('.data-table');

        tables.forEach(table => {
            // Evitar duplicar buscador
            if (table.previousElementSibling && table.previousElementSibling.classList.contains('table-search-container')) {
                return;
            }

            const searchContainer = document.createElement('div');
            searchContainer.className = 'table-search-container';
            searchContainer.style.marginBottom = '1rem';
            searchContainer.innerHTML = `
                <input type="text" class="form-control" placeholder="🔍 Buscar en la tabla..." style="max-width: 400px;">
            `;

            table.parentElement.insertBefore(searchContainer, table);

            const searchInput = searchContainer.querySelector('input');
            searchInput.addEventListener('input', function () {
                const searchTerm = this.value.toLowerCase();
                const tbody = table.querySelector('tbody');
                if (!tbody) return;
                const rows = tbody.querySelectorAll('tr');

                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            });
        });
    }

    addTableSearch();

    /* ===========================
       ANIMACIÓN STATS
       =========================== */
    function animateValue(element, start, end, duration) {
        if (isNaN(end)) {
            element.textContent = end;
            return;
        }
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            element.textContent = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    document.querySelectorAll('.stat-card-value').forEach(stat => {
        const original = parseInt(stat.textContent || '0', 10);
        if (isNaN(original)) return;
        stat.textContent = '0';
        animateValue(stat, 0, original, 1000);
    });

    /* ===========================
       RELOJ EN TOPBAR
       =========================== */
    function updateClock() {
        const topbarActions = document.querySelector('.topbar-actions');
        if (!topbarActions) return;

        const now = new Date();
        const timeString = now.toLocaleTimeString('es-PE', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        let clockElement = document.querySelector('.admin-clock');
        if (!clockElement) {
            clockElement = document.createElement('div');
            clockElement.className = 'admin-clock';
            clockElement.style.fontSize = '0.9rem';
            clockElement.style.color = '#666';
            topbarActions.prepend(clockElement);
        }

        clockElement.innerHTML = `<i class="bi bi-clock me-2"></i>${timeString}`;
    }

    setInterval(updateClock, 1000);
    updateClock();

    /* ===========================
       NOTIFICACIONES
       =========================== */
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '1rem 1.5rem';
        notification.style.borderRadius = '8px';
        notification.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        notification.style.zIndex = '9999';
        notification.style.animation = 'slideIn 0.3s ease';

        const colors = {
            success: '#4caf50',
            error: '#f44336',
            warning: '#ff9800',
            info: '#2196f3'
        };

        notification.style.background = colors[type] || colors.info;
        notification.style.color = 'white';
        notification.innerHTML = `
            <i class="bi bi-check-circle me-2"></i>
            <strong>${message}</strong>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    window.showNotification = showNotification; // por si lo quieres usar en otros scripts

    /* ===========================
       CSS ANIMACIONES NOTIFICACIONES
       =========================== */
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
        
        .badge {
            padding: 0.35rem 0.65rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        
        .bg-success {
            background: #4caf50 !important;
            color: white;
        }
        
        .bg-danger {
            background: #f44336 !important;
            color: white;
        }
        
        .bg-warning {
            background: #ff9800 !important;
            color: white;
        }
        
        .bg-info {
            background: #2196f3 !important;
            color: white;
        }
    `;
    document.head.appendChild(style);

    /* ===========================
       EXPORTAR TABLAS A CSV
       =========================== */
    function exportTableToCSV(tableContainerId, filename) {
        const container = document.getElementById(tableContainerId);
        if (!container) return;
        const table = container.querySelector('.data-table');
        if (!table) return;

        let csv = [];
        const rows = table.querySelectorAll('tr');

        rows.forEach(row => {
            const cols = row.querySelectorAll('td, th');
            const rowData = Array.from(cols).map(col => col.textContent.trim());
            csv.push(rowData.join(','));
        });

        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || 'export.csv';
        a.click();
        window.URL.revokeObjectURL(url);

        showNotification('Datos exportados exitosamente', 'success');
    }

    window.exportTableToCSV = exportTableToCSV;

    // Agregar botón "Exportar" a cada admin-card que tenga data-table
    document.querySelectorAll('.admin-card').forEach(card => {
        const table = card.querySelector('.data-table');
        const section = card.closest('.content-section');
        if (table && section && section.id) {
            const header = card.querySelector('.admin-card-header');
            if (header) {
                const exportBtn = document.createElement('button');
                exportBtn.type = 'button';
                exportBtn.className = 'btn-admin btn-sm';
                exportBtn.style.background = '#4caf50';
                exportBtn.innerHTML = '<i class="bi bi-download me-2"></i>Exportar';
                exportBtn.addEventListener('click', () => {
                    const cardTitle = header.querySelector('.admin-card-title')?.textContent?.trim() || 'export';
                    exportTableToCSV(section.id, `${cardTitle}.csv`);
                });
                header.appendChild(exportBtn);
            }
        }
    });

    /* ===========================
       ATAJOS DE TECLADO
       =========================== */
    document.addEventListener('keydown', function (e) {
        // Ctrl + S: simular guardar (primer botón .btn-admin que no sea eliminar)
        if (e.ctrlKey && (e.key === 's' || e.key === 'S')) {
            e.preventDefault();
            const saveButtons = Array.from(document.querySelectorAll('.btn-admin'))
                .filter(btn => !btn.classList.contains('btn-danger'));
            if (saveButtons.length > 0) {
                saveButtons[0].click();
                showNotification('Guardado ejecutado', 'success');
            }
        }

        // Ctrl + N: simular "Nuevo/Agregar"
        if (e.ctrlKey && (e.key === 'n' || e.key === 'N')) {
            e.preventDefault();
            const newButtons = document.querySelectorAll('.btn-admin');
            newButtons.forEach(btn => {
                if (btn.textContent.includes('Agregar') || btn.textContent.includes('Nuevo')) {
                    btn.click();
                }
            });
        }
    });

    console.log('Panel de administración cargado exitosamente');

    const reservasSection = document.getElementById('reservas');
    if (reservasSection) {
        if (reservasSection.classList.contains('active')) {
            cargarReservas();
        }
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.target.classList.contains('active')) {
                    cargarReservas();
                }
            });
        });
        observer.observe(reservasSection, { attributes: true, attributeFilter: ['class'] });
    }
});

function cargarReservas() {
    const estado = document.getElementById('filtroEstadoReserva')?.value || '';
    const fecha = document.getElementById('filtroFechaReserva')?.value || '';

    let url = '/admin/reservas/listar?';
    if (estado) url += `estado=${estado}&`;
    if (fecha) url += `fecha=${fecha}&`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            const tbody = document.getElementById('reservasBody');
            if (!tbody) return;

            if (!data.reservas || data.reservas.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">No hay reservas</td></tr>`;
                return;
            }

            tbody.innerHTML = data.reservas.map(r => {
                const [year, month, day] = r.fecha.split('-');
                const fecha = `${day}/${month}/${year}`;
                const horaInicio = r.hora_inicio?.substring(0, 5) || '';
                const horaFin = r.hora_fin?.substring(0, 5) || '';

                let badgeClass = 'bg-secondary';
                if (r.estado === 'pendiente') badgeClass = 'bg-warning';
                if (r.estado === 'confirmada') badgeClass = 'bg-success';
                if (r.estado === 'cancelada') badgeClass = 'bg-danger';
                if (r.estado === 'completada') badgeClass = 'bg-info';

                return `
                    <tr>
                        <td>${r.id}</td>
                        <td>${r.cancha_nombre}</td>
                        <td>${fecha}</td>
                        <td>${horaInicio} - ${horaFin}</td>
                        <td><strong>${r.cliente_nombre}</strong></td>
                        <td>${r.cliente_telefono}</td>
                        <td><span class="badge ${badgeClass}">${r.estado}</span></td>
                        <td>
                            <div class="btn-group">
                                ${r.estado === 'pendiente' ? `
                                    <form action="/admin/reservas/estado" method="POST" style="display:inline;">
                                        <input type="hidden" name="reserva_id" value="${r.id}">
                                        <input type="hidden" name="estado" value="confirmada">
                                        <button type="submit" class="btn-admin btn-sm btn-success" title="Confirmar">
                                            <i class="bi bi-check-lg"></i>
                                        </button>
                                    </form>
                                    <form action="/admin/reservas/estado" method="POST" style="display:inline;">
                                        <input type="hidden" name="reserva_id" value="${r.id}">
                                        <input type="hidden" name="estado" value="cancelada">
                                        <button type="submit" class="btn-admin btn-sm btn-danger" title="Cancelar">
                                            <i class="bi bi-x-lg"></i>
                                        </button>
                                    </form>
                                ` : ''}
                                ${r.estado === 'confirmada' ? `
                                    <form action="/admin/reservas/estado" method="POST" style="display:inline;">
                                        <input type="hidden" name="reserva_id" value="${r.id}">
                                        <input type="hidden" name="estado" value="completada">
                                        <button type="submit" class="btn-admin btn-sm btn-info" title="Marcar completada">
                                            <i class="bi bi-check-all"></i>
                                        </button>
                                    </form>
                                ` : ''}
                                <form action="/admin/reservas/eliminar/${r.id}" method="POST" style="display:inline;"
                                      onsubmit="return confirm('¿Eliminar esta reserva?');">
                                    <button type="submit" class="btn-admin btn-sm btn-outline-danger" title="Eliminar">
                                        <i class="bi bi-trash"></i>
                                    </button>
                                </form>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        })
        .catch(err => {
            console.error('Error cargando reservas:', err);
            const tbody = document.getElementById('reservasBody');
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">Error al cargar reservas</td></tr>`;
            }
        });
}
