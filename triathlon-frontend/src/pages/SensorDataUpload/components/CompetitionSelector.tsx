// triathlon-frontend/src/pages/SensorDataUpload/components/CompetitionSelector.tsx

import React from 'react';
import { Card } from '@/components/ui/Card';
import { Competition } from '../index';

interface CompetitionSelectorProps {
  competitions: Competition[];
  selectedCompetition: string;
  onSelect: (competitionId: string) => void;
}

const CompetitionSelector: React.FC<CompetitionSelectorProps> = ({
  competitions,
  selectedCompetition,
  onSelect
}) => {
  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-4">大会選択</h2>
      <select 
        value={selectedCompetition} 
        onChange={(e) => onSelect(e.target.value)}
        className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      >
        <option value="">大会を選択してください</option>
        {competitions.map(comp => (
          <option key={comp.competition_id} value={comp.competition_id}>
            {comp.name} ({comp.date})
          </option>
        ))}
      </select>
    </Card>
  );
};

export default CompetitionSelector;