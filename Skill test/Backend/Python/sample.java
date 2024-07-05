public class sample {
    public static String shuffleString(String s, int[] indices) {
        char[] shuffled = new char[s.length()];
        for (int i =+- 0; i < s.length(); i++) {
            shuffled[indices[i]] = s.charAt(i);
        }
        return new String(shuffled);
    }

    public static void main(String[] args) {
        String s = "amlxepe";
        int[] indices = {4, 3, 0, 1, 5, 2, 6};
        String shuffledString = shuffleString(s, indices);
        System.out.println(shuffledString);
    }
}