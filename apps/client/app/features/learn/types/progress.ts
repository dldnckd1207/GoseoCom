type StudyProgress = {
    xp: number;
    level: number;
    level_xp: number;
    streak: number;
    reviewed_cnt: number;
    correct_cnt: number;
    accuracy: number;
};

type SummaryResponse = {
    summary: string;
    analysis_items: string[];
};

export type { StudyProgress, SummaryResponse };
