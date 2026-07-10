<%@ page language="java" contentType="text/html; charset=UTF-8" %>
<%@ taglib uri="jakarta.tags.core" prefix="c" %>
<%@ taglib uri="jakarta.tags.fmt" prefix="fmt" %>

<%-- ============================================================
     Товар (name/price/фото) читается из online_shop (Java, ProductDAO).
     Отзывы/рейтинг/AI-сводка (объект ${summary}, тип AiSummary) читаются
     из sportmaster (Python-пайплайн) через SummaryDAO по product.modelId.
     Java только читает эти данные; запись (лайк/дизлайк, новый отзыв,
     фидбек к сводке) идёт через FastAPI — см. <script> внизу.
     ============================================================ --%>

<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>О товаре — ${product.name}</title>
    <link rel="icon" type="image/x-icon" href="${pageContext.request.contextPath}/favicon.ico">
    <link rel="icon" type="image/png" sizes="32x32" href="${pageContext.request.contextPath}/favicon-32.png">
    <link rel="apple-touch-icon" href="${pageContext.request.contextPath}/apple-touch-icon.png">
    <link rel="stylesheet" href="${pageContext.request.contextPath}/style/style.css?v=<%= System.currentTimeMillis() %>">
</head>
<body class="product-page">
    <jsp:include page="/WEB-INF/const/catalog_header.jsp"/>

    <main class="pi-main">
        <a class="back-link" href="${pageContext.request.contextPath}/catalog">← Назад к каталогу</a>

        <%-- ============ КАРТОЧКА ТОВАРА ============ --%>
        <section class="pi-top">
            <div class="pi-media">
                <div class="pi-photo"><img src="${pageContext.request.contextPath}/images/product${product.id}.jpg" alt="${product.name}"></div>
            </div>

            <div class="pi-info">
                <h1 class="pi-name">${product.name}</h1>
                <div class="pi-art">Арт. ${product.modelId != null ? product.modelId : product.id}</div>

                <div class="pi-rating">
                    <c:choose>
                        <c:when test="${summary != null && summary.reviewCount > 0}">
                            <span class="stars-rate stars-frac" id="piStars">
                                <span class="stars-bg">★★★★★</span>
                                <span class="stars-fg" id="piStarsFg" style="width:${summary.ratingPercent}%">★★★★★</span>
                            </span>
                            <span class="rate-num" id="piRateNum">${summary.ratingFormatted}</span>
                            <span class="rate-count" id="piRateCount">${summary.reviewCount} отзыва</span>
                        </c:when>
                        <c:otherwise>
                            <span class="rate-count">Пока нет отзывов</span>
                        </c:otherwise>
                    </c:choose>
                </div>

                <div class="pi-price">${product.priceFormatted} ₽</div>
            </div>
        </section>

        <%-- ---------- Описание (нерабочая заглушка со стрелкой) ---------- --%>
        <div class="accordion">
            <div class="acc-head">
                <span class="acc-title">Описание</span>
                <span class="acc-arrow">⌄</span>
            </div>
        </div>

        <%-- ---------- Характеристики (нерабочая заглушка со стрелкой) ---------- --%>
        <div class="accordion">
            <div class="acc-head">
                <span class="acc-title">Характеристики</span>
                <span class="acc-arrow">⌄</span>
            </div>
        </div>

        <%-- ============ ОТЗЫВЫ ============ --%>
        <section id="otzyvy" class="pi-section">
            <h2 class="pi-h2">Отзывы</h2>

            <div class="rev-grid">
                <c:if test="${summary != null && summary.reviewCount > 0}">
                <div class="rev-score">
                    <div class="rev-score-big" id="revScoreBig">${summary.ratingFormatted}</div>
                    <div class="stars-rate rev-score-stars stars-frac" id="revStars">
                        <span class="stars-bg">★★★★★</span>
                        <span class="stars-fg" id="revStarsFg" style="width:${summary.ratingPercent}%">★★★★★</span>
                    </div>
                    <div class="rev-score-count" id="revScoreCount">${summary.reviewCount} отзыва</div>
                </div>
                </c:if>

                <%-- Плашка AI-сводки: только если реально есть текст сводки и отзывов достаточно --%>
                <c:if test="${summary != null && not empty summary.aiSummary && summary.reviewCount >= 6}">
                <div class="ai-card" data-model-id="${product.modelId}">
                    <span class="ai-badge" tabindex="0">AI
                        <span class="ai-tooltip">Данный текст сгенерирован ИИ</span>
                    </span>

                    <div class="ai-card-title">Важное из отзывов</div>

                    <p class="ai-card-summary">${summary.aiSummary}</p>

                    <%-- Аспекты: сначала достоинства (pro), затем недостатки (con).
                         data-ids — реальные id отзывов из aspect_reviews, для фильтра ниже. --%>
                    <div class="ai-tags">
                        <c:forEach var="a" items="${summary.pros}" end="4">
                            <button class="ai-tag pro" onclick="filterByAspect(this)" data-aspect="${a.aspect}" data-ids="${a.reviewIdsCsv}"><span class="ai-tag-ic">✓</span> ${a.aspect} <span class="ai-tag-cnt">(${a.count})</span></button>
                        </c:forEach>
                        <c:forEach var="a" items="${summary.cons}" end="1">
                            <button class="ai-tag con" onclick="filterByAspect(this)" data-aspect="${a.aspect}" data-ids="${a.reviewIdsCsv}"><span class="ai-tag-ic">✕</span> ${a.aspect} <span class="ai-tag-cnt">(${a.count})</span></button>
                        </c:forEach>
                    </div>

                    <%-- Лайк/дизлайк идут через FastAPI (POST /api/products/{modelId}/summary/like|dislike) --%>
                    <div class="ai-feedback">
                        <a class="ai-fb-link" onclick="toggleFbForm()">Обратная связь</a>
                        <button class="like-btn" id="likeBtn" onclick="vote('like',this)">👍 <span>${summary.likes}</span></button>
                        <button class="like-btn" id="dislikeBtn" onclick="vote('dislike',this)">👎 <span>${summary.dislikes}</span></button>
                    </div>

                    <div id="fbForm" class="ai-fb-form" hidden>
                        <label>Напишите отзыв на сводку ИИ</label>
                        <textarea placeholder="Ваш комментарий к AI-сводке..."></textarea>
                        <button class="btn-primary" onclick="sendFb()">Отправить</button>
                    </div>
                </div>
                </c:if>
            </div>

            <button class="btn-primary open-review-btn" onclick="toggleReviewForm(this)">Оставить отзыв</button>

            <div class="new-review" id="newReview" hidden>
                <h3 class="nr-title">Оставьте отзыв о товаре</h3>

                <div class="nr-field">
                    <label>Ваше имя</label>
                    <input type="text" id="nrName" placeholder="Как к вам обращаться (необязательно)">
                </div>

                <div class="nr-field">
                    <label>Ваша оценка</label>
                    <div class="star-input" id="starInput">
                        <span data-v="1">★</span><span data-v="2">★</span><span data-v="3">★</span><span data-v="4">★</span><span data-v="5">★</span>
                    </div>
                </div>

                <div class="nr-field">
                    <label>Комментарий</label>
                    <textarea placeholder="Расскажите о вашем опыте использования товара..."></textarea>
                </div>

                <div class="nr-row">
                    <div class="nr-field">
                        <label>Достоинства</label>
                        <input type="text" id="nrPros" placeholder="Что понравилось">
                    </div>
                    <div class="nr-field">
                        <label>Недостатки</label>
                        <input type="text" id="nrCons" placeholder="Что можно улучшить">
                    </div>
                </div>

                <button class="btn-primary nr-submit" onclick="addReview()">Добавить отзыв</button>
                <p class="nr-hint" id="nrHint" style="display:none;font-size:13px;color:var(--muted,#5A6B84);margin-top:8px"></p>

                <div class="nr-progress" id="nrProgress" hidden>
                    <div class="nr-progress-track"><div class="nr-progress-fill" id="nrProgressFill"></div></div>
                    <p class="nr-progress-stage" id="nrProgressStage">Сохраняем отзыв…</p>
                </div>
            </div>

            <div id="filterBar" class="filter-bar" hidden>
                Показаны отзывы про: <b id="filterName"></b>
                <a class="filter-reset" onclick="resetFilter()">Сбросить фильтр ✕</a>
            </div>

            <%-- Реальные отзывы из sportmaster.reviews (последние ${summary.reviews.size()}) --%>
            <div class="review-list" id="reviewList">
                <c:forEach var="r" items="${summary.reviews}">
                    <div class="review-item" id="review-${r.reviewId}" data-id="${r.reviewId}">
                        <div class="review-head">
                            <span class="review-user">${not empty r.reviewerName ? r.reviewerName : 'Покупатель'}</span>
                            <c:if test="${r.rating != null}">
                                <span class="stars-rate review-stars"><c:forEach begin="1" end="5" var="i"><span class="${i <= r.stars ? 'st-on' : 'st-off'}">★</span></c:forEach></span>
                            </c:if>
                        </div>
                        <c:if test="${not empty r.pros || not empty r.cons}">
                        <div class="review-pc">
                            <c:if test="${not empty r.pros}"><span class="pc-pro">+ ${r.pros}</span></c:if>
                            <c:if test="${not empty r.cons}"><span class="pc-con">− ${r.cons}</span></c:if>
                        </div>
                        </c:if>
                        <p class="review-text">${r.text}</p>
                    </div>
                </c:forEach>
                <c:if test="${summary == null || empty summary.reviews}">
                    <p class="review-text">Отзывов пока нет.</p>
                </c:if>
            </div>

            <c:if test="${summary != null && summary.reviewCount > summary.reviews.size()}">
            <button class="btn-primary load-more-btn" id="loadMoreBtn" onclick="loadMoreReviews()">Загрузить ещё отзывы</button>
            </c:if>
        </section>
    </main>

    <jsp:include page="/WEB-INF/const/footer.jsp"/>

    <script>
    // ID модели в sportmaster (Python) — используется во всех вызовах API ниже.
    // Может быть пустым, если товар ещё не привязан к отзывам.
    const PRODUCT_ID = ${product.modelId != null ? product.modelId : 'null'};
    // Хост берём из адресной строки, а не хардкодим "localhost" — иначе с чужого
    // компьютера в локальной сети "localhost" будет означать его же машину, а не сервер.
    // Если страница открыта на стандартном порту (80/443) — значит, мы за nginx
    // (см. docker-compose), и он сам проксирует /api/* на бэкенд с того же origin.
    // Если порт указан явно (например :8080 при прямом запуске без Docker) — бэкенд
    // слушает отдельно на :8000, как раньше.
    const BEHIND_PROXY = window.location.port === "" || window.location.port === "80" || window.location.port === "443";
    const API_BASE = BEHIND_PROXY ? "" : ("http://" + window.location.hostname + ":8000");

    var reviewsLoaded = ${summary != null ? summary.reviews.size() : 0};
    var reviewsTotal = ${summary != null ? summary.reviewCount : 0};

    // === Построение разметки одного отзыва (используется и при добавлении своего, и при подгрузке) ===
    function reviewItemHtml(reviewerName, rating, pros, cons, text){
        var stars='';
        if(rating != null){
            var rounded = Math.round(rating);
            for(var i=1;i<=5;i++){ stars+='<span class="'+(i<=rounded?'st-on':'st-off')+'">★</span>'; }
            stars = '<span class="stars-rate review-stars">'+stars+'</span>';
        }
        var proscons='';
        if(pros) proscons += '<span class="pc-pro">+ '+escapeHtml(pros)+'</span>';
        if(cons) proscons += '<span class="pc-con">− '+escapeHtml(cons)+'</span>';
        return '<div class="review-head"><span class="review-user">'+escapeHtml(reviewerName || 'Покупатель')+'</span>'+stars+'</div>'+
            (proscons ? '<div class="review-pc">'+proscons+'</div>' : '')+
            '<p class="review-text">'+escapeHtml(text)+'</p>';
    }

    // === Подгрузка следующей порции отзывов («Загрузить ещё») ===
    function loadMoreReviews(){
        var btn=document.getElementById('loadMoreBtn');
        if(!PRODUCT_ID || !btn) return;
        btn.disabled=true;
        btn.textContent='Загружаем…';
        fetch(API_BASE + '/api/products/' + PRODUCT_ID + '/reviews?offset=' + reviewsLoaded + '&limit=30')
            .then(function(r){ return r.json(); })
            .then(function(list){
                var listEl=document.getElementById('reviewList');
                list.forEach(function(r){
                    var item=document.createElement('div');
                    item.className='review-item';
                    item.id='review-' + r.review_id;
                    item.dataset.id=r.review_id;
                    item.innerHTML=reviewItemHtml(r.reviewer_name, r.rating, r.pros, r.cons, r.text);
                    listEl.appendChild(item);
                });
                reviewsLoaded += list.length;
                btn.disabled=false;
                btn.textContent='Загрузить ещё отзывы';
                if(list.length < 30 || reviewsLoaded >= reviewsTotal){ btn.remove(); }
            })
            .catch(function(err){
                console.error(err);
                btn.disabled=false;
                btn.textContent='Не удалось загрузить, попробовать снова';
            });
    }

    // === Фильтрация отзывов по аспекту (id отзывов приходят из БД, см. data-ids) ===
    function filterByAspect(btn){
        var active=btn.classList.contains('active');
        document.querySelectorAll('.ai-tag').forEach(function(b){b.classList.remove('active');});
        if(active){ resetFilter(); return; }
        btn.classList.add('active');
        var ids=(btn.dataset.ids||'').split(',').map(function(x){return x.trim();}).filter(Boolean);
        var firstVisible=null;
        document.querySelectorAll('#reviewList .review-item').forEach(function(item){
            var show = ids.indexOf(item.dataset.id)>=0;
            item.style.display = show ? '' : 'none';
            if(show && !firstVisible) firstVisible=item;
        });
        var bar=document.getElementById('filterBar');
        document.getElementById('filterName').textContent=btn.dataset.aspect;
        bar.hidden=false;
        if(firstVisible) firstVisible.scrollIntoView({behavior:'smooth',block:'center'});
    }
    function resetFilter(){
        document.querySelectorAll('.ai-tag').forEach(function(b){b.classList.remove('active');});
        document.querySelectorAll('#reviewList .review-item').forEach(function(item){item.style.display='';});
        document.getElementById('filterBar').hidden=true;
    }

    // === Лайк/дизлайк сводки: один раз за сессию, пишет в БД через FastAPI ===
    var voted=false;
    function vote(kind, btn){
        if(voted || !PRODUCT_ID) return;
        voted=true;
        document.querySelectorAll('.like-btn').forEach(function(b){b.classList.add('disabled');});
        fetch(API_BASE + '/api/products/' + PRODUCT_ID + '/summary/' + kind, { method: 'POST' })
            .then(function(r){ return r.json(); })
            .then(function(data){
                document.querySelector('#likeBtn span').textContent = data.likes;
                document.querySelector('#dislikeBtn span').textContent = data.dislikes;
                btn.classList.add('chosen');
            })
            .catch(function(err){ console.error('Ошибка при отправке голоса', err); voted=false; });
    }

    // === Обратная связь по AI-сводке (текстовый комментарий) ===
    function toggleFbForm(){
        var f=document.getElementById('fbForm');
        f.hidden=!f.hidden;
    }
    function sendFb(){
        var f=document.getElementById('fbForm');
        var text=f.querySelector('textarea').value.trim();
        if(!text || !PRODUCT_ID){ f.innerHTML='<div class="fb-thanks">Спасибо! Отзыв о сводке отправлен.</div>'; return; }
        fetch(API_BASE + '/api/products/' + PRODUCT_ID + '/summary/feedback', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({text: text})
        }).finally(function(){
            f.innerHTML='<div class="fb-thanks">Спасибо! Отзыв о сводке отправлен.</div>';
        });
    }

    // === Форма нового отзыва ===
    function toggleReviewForm(btn){
        var f=document.getElementById('newReview');
        f.hidden=!f.hidden;
        btn.textContent=f.hidden?'Оставить отзыв':'Свернуть форму';
    }

    var chosen=0;
    (function(){
        var wrap=document.getElementById('starInput');
        var stars=wrap.querySelectorAll('span');
        stars.forEach(function(s){
            s.addEventListener('click',function(){
                chosen=+s.dataset.v;
                stars.forEach(function(x){x.classList.toggle('on',+x.dataset.v<=chosen);});
            });
        });
    })();

    // === Добавление отзыва: пишет в БД через FastAPI и отслеживает фоновый пересчёт AI-сводки ===
    function addReview(){
        var ta=document.querySelector('#newReview textarea');
        var text=ta.value.trim();
        var nameEl=document.getElementById('nrName');
        var prosEl=document.getElementById('nrPros');
        var consEl=document.getElementById('nrCons');
        var name=nameEl.value.trim();
        var pros=prosEl.value.trim();
        var cons=consEl.value.trim();
        var hint=document.getElementById('nrHint');
        var progress=document.getElementById('nrProgress');
        var progressFill=document.getElementById('nrProgressFill');
        var progressStage=document.getElementById('nrProgressStage');
        if(!chosen || !text){ alert('Поставьте оценку и напишите комментарий'); return; }
        if(!PRODUCT_ID){ alert('У этого товара пока нет привязки к отзывам.'); return; }

        var submitBtn=document.querySelector('.nr-submit');
        submitBtn.disabled = true;
        hint.style.display='none';
        progress.hidden=false;
        progressFill.style.width='5%';
        progressStage.textContent='Сохраняем отзыв…';

        // Отзыв в списке показываем сразу — не дожидаясь пересчёта сводки
        var displayName=name || 'Гость';
        var item=document.createElement('div');
        item.className='review-item flash';
        item.innerHTML=reviewItemHtml(displayName, chosen, pros, cons, text);
        document.getElementById('reviewList').insertBefore(item, document.getElementById('reviewList').firstChild);
        reviewsLoaded += 1;
        reviewsTotal += 1;

        var savedText=text, savedRating=chosen;
        ta.value=''; nameEl.value=''; prosEl.value=''; consEl.value=''; chosen=0;
        document.querySelectorAll('#starInput span').forEach(function(x){x.classList.remove('on');});

        fetch(API_BASE + '/api/products/' + PRODUCT_ID + '/reviews', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({text: savedText, rating: savedRating, pros: pros, cons: cons, name: name})
        })
        .then(function(r){ if(!r.ok) throw new Error('API error ' + r.status); return r.json(); })
        .then(function(data){ pollJob(data.job_id, progress, progressFill, progressStage, hint, submitBtn); })
        .catch(function(err){
            console.error(err);
            progress.hidden=true;
            hint.style.display='block';
            hint.textContent='Не удалось сохранить отзыв. Проверьте, что Python API запущен' + (BEHIND_PROXY ? ' и доступен через nginx.' : (' на ' + API_BASE + '.'));
            submitBtn.disabled=false;
        });
    }

    function escapeHtml(s){
        var d=document.createElement('div');
        d.textContent=s;
        return d.innerHTML;
    }

    // === Опрос статуса фонового пересчёта сводки (прогресс-бар) ===
    function pollJob(jobId, progress, progressFill, progressStage, hint, submitBtn){
        fetch(API_BASE + '/api/jobs/' + jobId)
            .then(function(r){ return r.json(); })
            .then(function(job){
                progressFill.style.width = job.progress + '%';
                progressStage.textContent = job.stage;
                if(job.status === 'running'){
                    setTimeout(function(){ pollJob(jobId, progress, progressFill, progressStage, hint, submitBtn); }, 700);
                } else if(job.status === 'done'){
                    if(job.summary) renderSummary(job.summary);
                    progressStage.textContent='Готово! AI-сводка обновлена.';
                    setTimeout(function(){ progress.hidden=true; }, 1500);
                    submitBtn.disabled=false;
                } else {
                    progress.hidden=true;
                    hint.style.display='block';
                    hint.textContent='Не удалось пересчитать сводку: ' + (job.error || 'неизвестная ошибка');
                    submitBtn.disabled=false;
                }
            })
            .catch(function(err){
                console.error(err);
                progress.hidden=true;
                hint.style.display='block';
                hint.textContent='Не удалось получить статус пересчёта сводки.';
                submitBtn.disabled=false;
            });
    }

    // === Обновление рейтинга/звёзд/счётчика отзывов после пересчёта ===
    function updateRatingDisplay(rating, reviewCount){
        var pct = Math.max(0, Math.min(100, rating / 5 * 100));
        var ratingStr = rating.toFixed(1).replace('.', ',');

        var piStarsFg=document.getElementById('piStarsFg');
        if(piStarsFg) piStarsFg.style.width = pct + '%';
        var piRateNum=document.getElementById('piRateNum');
        if(piRateNum) piRateNum.textContent = ratingStr;
        var piRateCount=document.getElementById('piRateCount');
        if(piRateCount) piRateCount.textContent = reviewCount + ' отзыва';

        var revStarsFg=document.getElementById('revStarsFg');
        if(revStarsFg) revStarsFg.style.width = pct + '%';
        var revScoreBig=document.getElementById('revScoreBig');
        if(revScoreBig) revScoreBig.textContent = ratingStr;
        var revScoreCount=document.getElementById('revScoreCount');
        if(revScoreCount) revScoreCount.textContent = reviewCount + ' отзыва';
    }

    // === Перерисовка карточки AI-сводки после пересчёта, без перезагрузки страницы ===
    function renderSummary(summary){
        var card=document.querySelector('.ai-card');
        if(!card){
            var grid=document.querySelector('.rev-grid');
            card=document.createElement('div');
            card.className='ai-card';
            card.setAttribute('data-model-id', PRODUCT_ID);
            card.innerHTML='<span class="ai-badge" tabindex="0">AI<span class="ai-tooltip">Данный текст сгенерирован ИИ</span></span>'+
                '<div class="ai-card-title">Важное из отзывов</div>'+
                '<p class="ai-card-summary"></p>'+
                '<div class="ai-tags"></div>'+
                '<div class="ai-feedback">'+
                '<a class="ai-fb-link" onclick="toggleFbForm()">Обратная связь</a>'+
                '<button class="like-btn" id="likeBtn" onclick="vote(\'like\',this)">👍 <span>0</span></button>'+
                '<button class="like-btn" id="dislikeBtn" onclick="vote(\'dislike\',this)">👎 <span>0</span></button>'+
                '</div>'+
                '<div id="fbForm" class="ai-fb-form" hidden><label>Напишите отзыв на сводку ИИ</label>'+
                '<textarea placeholder="Ваш комментарий к AI-сводке..."></textarea>'+
                '<button class="btn-primary" onclick="sendFb()">Отправить</button></div>';
            grid.appendChild(card);
        }

        card.querySelector('.ai-card-summary').textContent = summary.ai_summary || '';
        document.querySelector('#likeBtn span').textContent = summary.ai_summary_likes;
        reviewsTotal = summary.review_count;
        updateRatingDisplay(summary.rating, summary.review_count);
        document.querySelector('#dislikeBtn span').textContent = summary.ai_summary_dislikes;

        var tags=card.querySelector('.ai-tags');
        tags.innerHTML='';
        (summary.pros || []).slice(0, 5).forEach(function(a){ tags.appendChild(buildAspectButton(a, 'pro')); });
        (summary.cons || []).slice(0, 2).forEach(function(a){ tags.appendChild(buildAspectButton(a, 'con')); });
    }

    function buildAspectButton(aspect, kind){
        var btn=document.createElement('button');
        btn.className='ai-tag ' + kind;
        btn.onclick=function(){ filterByAspect(btn); };
        btn.dataset.aspect=aspect.aspect;
        btn.dataset.ids=(aspect.review_ids || []).join(',');
        btn.innerHTML='<span class="ai-tag-ic">'+(kind==='pro'?'✓':'✕')+'</span> '+escapeHtml(aspect.aspect)+' <span class="ai-tag-cnt">('+aspect.count+')</span>';
        return btn;
    }
    </script>
</body>
</html>
