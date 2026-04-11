/* ix.js — Index Comparison Charts */
(function () {
    'use strict';

    const d = window.__IX__;
    if (!d) return;

    const C = {
        stock:        '#38bdf8',
        index:        '#f5a623',
        alpha:        '#a78bfa',
        rs:           '#22c55e',
        rs_ma:        '#4a5568',
        paper:        '#06090f',
        plot:         '#05080e',
        grid:         'rgba(255,255,255,0.05)',
        zero:         'rgba(255,255,255,0.08)',
        text:         '#3a4460',
        hover_bg:     '#0d1117',
        hover_border: '#1e2330',
    };

    function isMobileView() {
        const width = el ? el.offsetWidth : window.innerWidth;
        return width <= 768;
    }

    function getBaseLayout() {
        const mobile = isMobileView();

        return {
            paper_bgcolor: C.paper,
            plot_bgcolor:  C.plot,
            margin: mobile ? { l: 8, r: 12, t: 8, b: 28 } : { l: 10, r: 64, t: 10, b: 36 },
            hovermode: 'x unified',
            hoverlabel: {
                bgcolor:     C.hover_bg,
                bordercolor: C.hover_border,
                font: { family: 'Arial, sans-serif', size: mobile ? 11 : 12, color: '#e2e8f0' },
                namelength: -1,
            },
            showlegend: false,
            xaxis: {
                showgrid: false, zeroline: false,
                color: C.text,
                tickfont: { size: mobile ? 9 : 10, color: C.text },
                showspikes: !mobile,
                spikecolor: 'gray',
                spikemode: 'across',
                spikesnap: 'cursor',
                nticks: mobile ? 4 : undefined,
                automargin: true,
            },
            yaxis: {
                side: 'right', showgrid: true, gridcolor: C.grid,
                zeroline: false, color: C.text,
                tickfont: { size: mobile ? 9 : 10, color: C.text },
                tickformat: '.2f',
                nticks: mobile ? 5 : undefined,
                automargin: true,
            },
        };
    }

    function lastVal(arr) {
        for (let i = arr.length - 1; i >= 0; i--) {
            if (arr[i] !== null && arr[i] !== undefined) return arr[i];
        }
        return null;
    }

    function endLabel(dates, arr, color, text) {
        if (isMobileView()) return null;
        const lv = lastVal(arr);
        if (lv === null) return null;
        return {
            x: dates[dates.length - 1], y: lv,
            xanchor: 'left', yanchor: 'middle',
            text: `<b>${text}</b>`, showarrow: false,
            font: { color, size: 11, family: 'Arial' }, xshift: 8,
        };
    }

    function zeroLine(dates) {
        return {
            x: [dates[0], dates[dates.length - 1]], y: [0, 0],
            type: 'scatter', mode: 'lines',
            line: { color: C.zero, width: 1 },
            hoverinfo: 'skip', showlegend: false,
        };
    }

    /* ── Race ── */
    function chartRace() {
        const base = getBaseLayout();
        const ls = lastVal(d.stock_normalized);
        const li = lastVal(d.index_normalized);
        const anns = [
            endLabel(d.dates, d.stock_normalized, C.stock,
                (ls - 100 >= 0 ? '+' : '') + (ls - 100).toFixed(1) + '%'),
            endLabel(d.dates, d.index_normalized, C.index,
                (li - 100 >= 0 ? '+' : '') + (li - 100).toFixed(1) + '%'),
        ].filter(Boolean);
        return {
            traces: [
                {
                    x: d.dates, y: d.index_normalized, name: d.index_name,
                    type: 'scatter', mode: 'lines',
                    line: { color: C.index, width: 1.5, dash: 'dot' },
                    hovertemplate: `<b>${d.index_name}</b> %{y:.2f}<extra></extra>`,
                },
                {
                    x: d.dates, y: d.stock_normalized, name: d.stock_name,
                    type: 'scatter', mode: 'lines',
                    line: { color: C.stock, width: 2 },
                    fill: 'tonexty', fillcolor: 'rgba(56,189,248,0.06)',
                    hovertemplate: `<b>${d.stock_name}</b> %{y:.2f}<extra></extra>`,
                },
                { x: [d.dates[0], d.dates[d.dates.length-1]], y: [100,100],
                  type:'scatter', mode:'lines', line:{color:C.zero,width:1},
                  hoverinfo:'skip', showlegend:false },
            ],
            layout: { ...base, annotations: anns },
            caption: `Normalized to 100 at start · ${d.stock_name} (blue) vs ${d.index_name} (amber)`,
        };
    }

    /* ── Cumulative Alpha ── */
    function chartCumAlpha() {
        const base = getBaseLayout();
        const lv = lastVal(d.alpha_cumulative);
        const ann = endLabel(d.dates, d.alpha_cumulative, C.alpha,
            (lv >= 0 ? '+' : '') + lv.toFixed(2));
        return {
            traces: [
                { x: d.dates, y: d.alpha_cumulative.map(() => 0),
                  type:'scatter', mode:'lines', line:{color:'transparent',width:0},
                  hoverinfo:'skip', showlegend:false },
                {
                    x: d.dates, y: d.alpha_cumulative, name: 'Cumulative Alpha',
                    type: 'scatter', mode: 'lines',
                    line: { color: C.alpha, width: 2 },
                    fill: 'tonexty', fillcolor: 'rgba(167,139,250,0.07)',
                    hovertemplate: `Alpha %{y:+.2f}<extra></extra>`,
                },
                zeroLine(d.dates),
            ],
            layout: {
                ...base,
                annotations: ann ? [ann] : [],
                yaxis: { ...base.yaxis, tickformat: '+.2f' },
            },
            caption: 'Cumulative alpha = stock normalized − index normalized. Above zero = stock is ahead.',
        };
    }

    /* ── Rolling Alpha ── */
    function chartRolling() {
        const base = getBaseLayout();
        return {
            traces: [
                { x: d.dates, y: d.alpha_rolling.map(() => 0),
                  type:'scatter', mode:'lines', line:{color:'transparent',width:0},
                  hoverinfo:'skip', showlegend:false },
                {
                    x: d.dates, y: d.alpha_rolling, name: '20d Rolling Alpha',
                    type: 'scatter', mode: 'lines',
                    line: { color: C.stock, width: 2 },
                    fill: 'tonexty', fillcolor: 'rgba(56,189,248,0.07)',
                    hovertemplate: `Rolling α %{y:+.3f}%<extra></extra>`,
                },
                zeroLine(d.dates),
            ],
            layout: {
                ...base,
                shapes: [{ type:'line', x0:d.dates[0], x1:d.dates[d.dates.length-1],
                    y0:0, y1:0, xref:'x', yref:'y',
                    line:{ color:'rgba(255,255,255,0.12)', width:1 } }],
                yaxis: { ...base.yaxis, tickformat: '+.3f' },
            },
            caption: '20-day rolling mean of daily alpha (%). Positive = stock outpacing index on a rolling basis.',
        };
    }

    /* ── Relative Strength ── */
    function chartRS() {
        const base = getBaseLayout();
        const lv = lastVal(d.relative_strength);
        const ann = endLabel(d.dates, d.relative_strength, C.rs, lv.toFixed(4));
        return {
            traces: [
                {
                    x: d.dates, y: d.rs_ma, name: 'RS 20d MA',
                    type: 'scatter', mode: 'lines',
                    line: { color: C.rs_ma, width: 1.5, dash: 'dot' },
                    hovertemplate: `RS MA %{y:.4f}<extra></extra>`,
                },
                {
                    x: d.dates, y: d.relative_strength, name: 'Relative Strength',
                    type: 'scatter', mode: 'lines',
                    line: { color: C.rs, width: 2 },
                    hovertemplate: `RS %{y:.4f}<extra></extra>`,
                },
            ],
            layout: {
                ...base,
                annotations: ann ? [ann] : [],
                yaxis: { ...base.yaxis, tickformat: '.4f' },
            },
            caption: 'Relative Strength = stock / index (normalized). Rising = stock leading. Dotted = 20d MA.',
        };
    }

    /* ── RENDER ── */
    const el      = document.getElementById('ix-chart');
    const caption = document.getElementById('ix-caption');
    if (!el) return;

    const CHARTS = { race: chartRace, cumulative: chartCumAlpha, rolling: chartRolling, rs: chartRS };
    let plotted = false;
    let currentKey = 'race';

    function render(key) {
        const elH = el.offsetHeight;
        // Guard: if height is 0, element isn't laid out yet — defer
        if (elH === 0) {
            setTimeout(() => render(key), 50);
            return;
        }
        const c = CHARTS[key]();
        const layout = { ...c.layout, height: elH };
        if (!plotted) {
            Plotly.newPlot(el, c.traces, layout, {
                displayModeBar: false, responsive: true, scrollZoom: false,
            });
            plotted = true;
        } else {
            Plotly.react(el, c.traces, layout);
        }
        if (caption) caption.textContent = c.caption;
    }

    document.querySelectorAll('.ix-tab').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.ix-tab').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentKey = btn.dataset.chart;
            render(currentKey);
        });
    });

    // Render after page fully loaded so element has height
    if (document.readyState === 'complete') {
        render('race');
    } else {
        window.addEventListener('load', () => render('race'));
    }

    window.addEventListener('resize', () => {
        if (plotted) render(currentKey);
    });

})();
