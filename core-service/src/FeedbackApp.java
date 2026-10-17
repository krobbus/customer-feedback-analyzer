package src;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Scanner;

public class FeedbackApp {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);

        System.out.println("==================================================");
        System.out.println("   AI-Powered Batch Customer Feedback System      ");
        System.out.println("==================================================");
        System.out.print("Enter path to feedback CSV file (.csv): ");
        String filePath = scanner.nextLine().trim();

        if (filePath.isEmpty()) {
            System.out.println("[Error]: File path cannot be empty.");
            scanner.close();
            return;
        }

        filePath = filePath.replace("\"", "");

        try {
            System.out.println("\n[System]: Handing over file to Python batch processor...\n");

            ProcessBuilder processBuilder = new ProcessBuilder(
                    "python",
                    "ai-service/scripts/batch_csv.py",
                    filePath);

            processBuilder.redirectErrorStream(true);
            Process process = processBuilder.start();

            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println(line);
            }

            int exitCode = process.waitFor();
            if (exitCode != 0) {
                System.out.println("\n[Error]: Python batch processor exited with code " + exitCode);
            }

        } catch (Exception e) {
            System.out.println("[Exception]: Failed to execute Python batch process.");
            e.printStackTrace();
        } finally {
            scanner.close();
        }
    }
}