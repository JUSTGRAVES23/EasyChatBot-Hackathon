export interface LearningWorld {

  id: string;

  name: string;

  flag: string;

  color: string;

  description: string;

  primaryLanguage: string;

  secondaryLanguage: string;

  unlocked: boolean;

}



export const LEARNING_WORLDS: LearningWorld[] = [


  {
    id: "french",

    name: "French World",

    flag: "🇫🇷",

    color: "#2455E6",

    description:
      "Discover French language, culture, conversations and new adventures.",

    primaryLanguage: "French",

    secondaryLanguage: "English",

    unlocked: true,
  },



  {
    id: "spanish",

    name: "Spanish World",

    flag: "🇪🇸",

    color: "#E30613",

    description:
      "Explore Spanish language, culture and real conversations.",

    primaryLanguage: "Spanish",

    secondaryLanguage: "English",

    unlocked: true,
  },



  {
    id: "english",

    name: "English World",

    flag: "🇬🇧",

    color: "#2455E6",

    description:
      "Master English through immersive adventures.",

    primaryLanguage: "English",

    secondaryLanguage: "Spanish",

    unlocked: false,
  },



  {
    id: "german",

    name: "German World",

    flag: "🇩🇪",

    color: "#111111",

    description:
      "German adventures coming soon.",

    primaryLanguage: "German",

    secondaryLanguage: "English",

    unlocked: false,
  },


];