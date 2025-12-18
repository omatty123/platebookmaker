const platebook = {
  course: "HIST 213 East Asia in the Modern World",
  term: "Winter 2026",
  plates: [
    { title: "Introduction to the class, geography", date: "Jan 6", full: true },
    { title: "East Asian Language, Religion, Culture", date: "Jan 8", full: true },
    { title: "What is Modernity?", date: "Jan 10", full: true },
    { title: "Joseon Invaded", date: "Jan 13", full: true },
    { title: "Rise of Qing, Creation of Manchu Empire", date: "Jan 15", full: true },
    { title: "Qing's Encounter with the West", date: "Jan 17", full: true },
    { title: "Joseon Reform", date: "Jan 22", full: true },
    { title: "Rise of Tokugawa", date: "Jan 24", full: true },
    { title: "Final presentation brainstorm / Current events", date: "Jan 27", full: true },
    { title: "Qing vs. the West", date: "Jan 29", full: true },
    { title: "Tokugawa vs. the West", date: "Jan 31", full: true },
    { title: "Meiji “Transformation”", date: "Feb 3", full: true },
    { title: "Taiping and other rebellions", date: "Feb 5", full: true },
    { title: "Tonghak Rebellion", date: "Feb 7", full: true },
    { title: "Joseon's Slow Evolution", date: "Feb 10", full: true },
    { title: "Tonghak in Film", date: "Feb 12", full: true },
    { title: "Japanese Nationalism – Rise of an empire", date: "Feb 17", full: true },
    { title: "Korean Nationalism – Rise of a nation", date: "Feb 19", full: true },
    { title: "Chinese Nationalism – “modernity” at gunpoint", date: "Feb 21", full: true },
    { title: "The Pacific War", date: "Feb 24", full: true },
    { title: "Civil War and Revolution in China", date: "Feb 26", full: true },
    { title: "Rebuilding Japan", date: "Feb 28", full: true },
    { title: "Mao and Beyond Mao", date: "March 3", full: true },
    { title: "Liberation, Division, Rebuilding Korea", date: "March 5", full: true },
    { title: "Japan rises again", date: "March 7", full: true },

    // Notes-only plates (A)
    { title: "Final presentations", date: "March 10", full: false },
    { title: "Final presentations", date: "March 12", full: false },
    { title: "Final presentations", date: "March 14", full: false }
  ].map(p => ({
    ...p,
    person: "",
    place: "",
    thing: "",
    timeline: "",
    map: "",
    questions: [
      { q: "", a: "" },
      { q: "", a: "" }
    ],
    causesEffectsConnections: "",
    notes: ""
  }))
};
