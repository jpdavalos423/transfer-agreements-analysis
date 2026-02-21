import { GeneratePathwayResponse, PlanCourse, PlanTerm } from "../types";

interface Props {
  response: GeneratePathwayResponse;
}

export interface PlanMetrics {
  termCount: number;
  courseCount: number;
  overallUnits: number;
}

function toUnitNumber(value: number | string): number {
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

function formatUnits(units: number): string {
  const rounded = Math.round(units * 100) / 100;
  if (Number.isInteger(rounded)) {
    return String(rounded);
  }
  return rounded.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
}

function normalizeTerm(term: PlanTerm): { term: string; courses: Array<{ courseCode: string; units: number }> } {
  const termName = typeof term?.term === "string" && term.term.trim() !== "" ? term.term : "Unnamed Term";
  const courses = Array.isArray(term?.courses) ? term.courses : [];
  const normalizedCourses = courses.map((course: PlanCourse) => ({
    courseCode:
      typeof course?.courseCode === "string" && course.courseCode.trim() !== ""
        ? course.courseCode
        : "UNKNOWN",
    units: toUnitNumber(course?.units),
  }));
  return {
    term: termName,
    courses: normalizedCourses,
  };
}

export function calculatePlanMetrics(response: GeneratePathwayResponse): PlanMetrics {
  const plan = Array.isArray(response?.plan) ? response.plan : [];
  const normalizedTerms = plan.map((term) => normalizeTerm(term));
  const termUnits = normalizedTerms.map((term) =>
    term.courses.reduce((sum, course) => sum + course.units, 0),
  );
  return {
    termCount: normalizedTerms.length,
    courseCount: normalizedTerms.reduce((sum, term) => sum + term.courses.length, 0),
    overallUnits: termUnits.reduce((sum, units) => sum + units, 0),
  };
}

export function ResultsView({ response }: Props) {
  const plan = Array.isArray(response?.plan) ? response.plan : [];

  if (plan.length === 0) {
    return (
      <p className="results-empty">
        No pathway terms were returned. Try adding more targets or fewer completed constraints.
      </p>
    );
  }

  const normalizedTerms = plan.map((term) => normalizeTerm(term));
  const termUnits = normalizedTerms.map((term) =>
    term.courses.reduce((sum, course) => sum + course.units, 0),
  );
  const metrics = calculatePlanMetrics(response);

  return (
    <>
      <p className="results-summary">Overall Units: {formatUnits(metrics.overallUnits)}</p>
      {normalizedTerms.map((term, termIndex) => (
        <article className="term-card" key={`${term.term}-${termIndex}`}>
          <div className="term-header">
            <h3 className="term-title">{term.term}</h3>
            <p className="term-units">Term Units: {formatUnits(termUnits[termIndex])}</p>
          </div>
          <ul className="term-courses">
            {term.courses.map((course, courseIndex) => (
              <li className="term-course-item" key={`${course.courseCode}-${courseIndex}`}>
                <span className="course-code">{course.courseCode}</span>
                <span className="course-units">{formatUnits(course.units)} units</span>
              </li>
            ))}
          </ul>
        </article>
      ))}
    </>
  );
}
