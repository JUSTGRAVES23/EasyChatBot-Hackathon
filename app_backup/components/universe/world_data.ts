export interface LearningWorld {

id:string;

name:string;

flag:string;

color:string;

description:string;

unlocked:boolean;

}



export const LEARNING_WORLDS:LearningWorld[] = [


{
id:"french",
name:"French World",
flag:"🇫🇷",
color:"#2455E6",
description:
"Explore French language, culture and conversations.",
unlocked:true
},


{
id:"spanish",
name:"Spanish World",
flag:"🇪🇸",
color:"#E5A000",
description:
"A new language adventure coming soon.",
unlocked:false
}


];