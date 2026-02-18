function toUnitNumber(value) {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return 0;
}

export function formatUnits(units) {
  const rounded = Math.round(units * 100) / 100;
  if (Number.isInteger(rounded)) {
    return String(rounded);
  }
  return rounded.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
}

export function buildResultsViewModel(responsePayload) {
  const plan = Array.isArray(responsePayload?.plan) ? responsePayload.plan : [];
  if (plan.length === 0) {
    return {
      isEmpty: true,
      emptyMessage:
        "No pathway terms were returned. Try adding more targets or fewer completed constraints.",
      terms: [],
      overallUnits: 0,
    };
  }

  const terms = plan.map((term) => {
    const termName =
      typeof term?.term === "string" && term.term.trim() !== ""
        ? term.term
        : "Unnamed Term";
    const courses = Array.isArray(term?.courses) ? term.courses : [];
    const normalizedCourses = courses.map((course) => ({
      courseCode:
        typeof course?.courseCode === "string" && course.courseCode.trim() !== ""
          ? course.courseCode
          : "UNKNOWN",
      units: toUnitNumber(course?.units),
    }));
    const termUnits = normalizedCourses.reduce((sum, course) => sum + course.units, 0);
    return {
      term: termName,
      courses: normalizedCourses,
      termUnits,
    };
  });

  const overallUnits = terms.reduce((sum, term) => sum + term.termUnits, 0);
  return {
    isEmpty: false,
    emptyMessage: "",
    terms,
    overallUnits,
  };
}

export function renderResults(containerEl, responsePayload) {
  if (!containerEl) {
    return;
  }

  containerEl.innerHTML = "";
  const model = buildResultsViewModel(responsePayload);

  if (model.isEmpty) {
    const empty = document.createElement("p");
    empty.className = "results-empty";
    empty.textContent = model.emptyMessage;
    containerEl.appendChild(empty);
    return;
  }

  const summary = document.createElement("p");
  summary.className = "results-summary";
  summary.textContent = `Overall Units: ${formatUnits(model.overallUnits)}`;
  containerEl.appendChild(summary);

  for (const term of model.terms) {
    const termCard = document.createElement("article");
    termCard.className = "term-card";

    const termHeader = document.createElement("div");
    termHeader.className = "term-header";

    const termTitle = document.createElement("h3");
    termTitle.className = "term-title";
    termTitle.textContent = term.term;

    const termUnits = document.createElement("p");
    termUnits.className = "term-units";
    termUnits.textContent = `Term Units: ${formatUnits(term.termUnits)}`;

    termHeader.appendChild(termTitle);
    termHeader.appendChild(termUnits);
    termCard.appendChild(termHeader);

    const courseList = document.createElement("ul");
    courseList.className = "term-courses";
    for (const course of term.courses) {
      const item = document.createElement("li");
      item.className = "term-course-item";

      const courseCode = document.createElement("span");
      courseCode.className = "course-code";
      courseCode.textContent = course.courseCode;

      const courseUnits = document.createElement("span");
      courseUnits.className = "course-units";
      courseUnits.textContent = `${formatUnits(course.units)} units`;

      item.appendChild(courseCode);
      item.appendChild(courseUnits);
      courseList.appendChild(item);
    }

    termCard.appendChild(courseList);
    containerEl.appendChild(termCard);
  }
}

