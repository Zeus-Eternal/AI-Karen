
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import TextSelectionTest from '@/components/debug/TextSelectionTest';
import ModelAvailabilityCheck from '@/components/debug/ModelAvailabilityCheck';

export default function DebugPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">AI-Karen Debug Tools</h1>
      
      <Tabs defaultValue="models" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="models">Model Availability</TabsTrigger>
          <TabsTrigger value="text-selection">Text Selection</TabsTrigger>
        </TabsList>
        
        <TabsContent value="models" className="mt-6">
          <ModelAvailabilityCheck />
        </TabsContent>
        
        <TabsContent value="text-selection" className="mt-6">
          <TextSelectionTest />
        </TabsContent>
      </Tabs>
    </div>
  );
}