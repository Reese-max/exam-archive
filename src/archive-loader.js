/* Small, dependency-free loader for the static archive assets. */
(function (global) {
  const YEARS = ["114", "113", "112", "111", "110", "109", "108", "107", "106", "105"];

  function createArchiveLoader(fetchImpl) {
    const requests = new Map();

    function load(url) {
      if (!requests.has(url)) {
        const request = fetchImpl(url).then(response => {
          if (!response || !response.ok) {
            throw new Error(`Archive request failed: ${url} (${response ? response.status : "no response"})`);
          }
          return response.text();
        }).catch(error => {
          requests.delete(url);
          throw error;
        });
        requests.set(url, request);
      }
      return requests.get(url);
    }

    return {
      loadYear(year) {
        const value = String(year);
        if (!YEARS.includes(value)) return Promise.reject(new Error(`Unknown archive year: ${value}`));
        return load(`data/year-${value}.txt`);
      },
      loadCategory(slug, year) {
        const value = String(year);
        if (!YEARS.includes(value)) return Promise.reject(new Error(`Unknown archive year: ${value}`));
        if (!/^[a-z-]+$/.test(slug)) return Promise.reject(new Error(`Unknown subject: ${slug}`));
        return load(`data/subjects/${slug}/year-${value}.txt`);
      },
      loadSearchScope() {
        return Promise.all(YEARS.map(year => this.loadYear(year)));
      },
      loadedRequests() {
        return [...requests.keys()];
      },
      years: [...YEARS],
    };
  }

  function bindSearchShortcuts(document, input, clearSearch) {
    document.addEventListener("keydown", event => {
      const target = event.target;
      const typing = target && typeof target.closest === "function" && target.closest("input,textarea,[contenteditable=true]");
      if (((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") || (event.key === "/" && !typing)) {
        event.preventDefault();
        input.focus();
      }
      if (event.key === "Escape" && document.activeElement === input) {
        input.value = "";
        clearSearch("");
        input.blur();
      }
    });
  }

  global.createArchiveLoader = createArchiveLoader;
  global.bindArchiveSearchShortcuts = bindSearchShortcuts;
})(window);
